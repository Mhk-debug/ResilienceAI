"""
services/retrieval/retriever.py

The main retrieval orchestrator. Accepts structured assessment data and returns
the most relevant knowledge chunks from the existing ChromaDB vector index.

Designed as an independent component with a simple public interface
so it can be plugged into the LLM pipeline without coupling.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from project_schema import BuildingLLMContext, EnvironmentalContext

from .embedder import Embedder
from .indexer import Indexer, COLLECTION_NAME
from .query_builder import ChannelQuery, QueryBuilder

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────────────────────


@dataclass
class RetrievalResult:
    """
    A single retrieved knowledge chunk with relevance information.

    Attributes:
        chunk_id: Unique identifier of the chunk in ChromaDB.
        text: The chunk text content.
        score: Relevance score (cosine similarity, 0–1).
        metadata: Metadata dict stored in ChromaDB for this chunk.
        channel: Which retrieval channel produced this result.
    """

    chunk_id: str
    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    channel: str = ""


# ──────────────────────────────────────────────────────────────
# Retriever
# ──────────────────────────────────────────────────────────────


class Retriever:
    """
    Retrieves relevant knowledge chunks for a building assessment.

    Uses ChromaDB semantic search with per-channel queries constructed
    from structured assessment data. Supports metadata-based score boosting
    to prefer chunks whose tags match the building's characteristics.

    Usage::

        retriever = Retriever(indexer, embedder)
        results = retriever.retrieve(building_ctx, env_ctx)
    """

    def __init__(
        self,
        indexer: Indexer,
        embedder: Optional[Embedder] = None,
    ):
        """
        Args:
            indexer: An Indexer instance with a loaded ChromaDB collection.
            embedder: Embedder for query encoding. If None, creates a default one.
        """
        self.indexer = indexer
        self.embedder = embedder or Embedder()
        self.query_builder = QueryBuilder()

        # Collection is lazily loaded; will be set on first retrieve call
        self._collection: Any = None

    # ── Public API ───────────────────────────────────────────

    def retrieve(
        self,
        building: BuildingLLMContext,
        env: EnvironmentalContext,
    ) -> List[RetrievalResult]:
        """
        Retrieve the most relevant knowledge chunks for an assessment.

        Args:
            building: Building structural and material context.
            env: Environmental hazard context.

        Returns:
            A list of ``RetrievalResult``, ordered by relevance descending.
            Returns an empty list if retrieval fails or the index is unavailable.
        """
        try:
            collection = self._get_collection()
        except (FileNotFoundError, RuntimeError) as e:
            logger.warning("Retrieval unavailable (index not loaded): %s", e)
            return []
        except Exception as e:
            logger.warning("Unexpected error accessing index: %s", e)
            return []

        # Build per-channel queries
        try:
            channels = self.query_builder.build(building, env)
        except Exception as e:
            logger.warning("Query building failed: %s", e)
            return []

        # Retrieve results from each channel
        all_results: List[RetrievalResult] = []
        for channel in channels:
            try:
                channel_results = self._search_channel(collection, channel)
                all_results.extend(channel_results)
            except Exception as e:
                logger.warning(
                    "Channel '%s' retrieval failed: %s",
                    channel.channel_name,
                    e,
                )
                continue

        # Deduplicate: keep the highest-scoring occurrence of each chunk
        seen_ids: set[str] = set()
        unique_results: List[RetrievalResult] = []
        for result in sorted(all_results, key=lambda r: r.score, reverse=True):
            if result.chunk_id not in seen_ids:
                seen_ids.add(result.chunk_id)
                unique_results.append(result)

        logger.info(
            "Retrieved %d unique chunks from %d channels",
            len(unique_results),
            len(channels),
        )
        return unique_results

    def is_available(self) -> bool:
        """
        Check whether the retriever has a valid index available.

        Returns:
            True if the index exists and is non-empty.
        """
        try:
            return self.indexer.index_exists()
        except Exception:
            return False

    # ── Internal: ChromaDB Search ────────────────────────────

    def _search_channel(
        self,
        collection: Any,
        channel: ChannelQuery,
    ) -> List[RetrievalResult]:
        """
        Execute a single channel query against ChromaDB.

        Performs a semantic search and optionally boosts scores for chunks
        whose tags match the query's ``tags_filter``.
        """
        if not channel.query.strip():
            logger.debug("Empty query for channel '%s', skipping", channel.channel_name)
            return []

        # Encode the query text
        query_vector = self.embedder.embed_single(channel.query)

        # ChromaDB query with category filter
        n_results = max(channel.k * 10, 20)  # Get more candidates for re-ranking
        where_filter = {"category": {"$in": channel.category_filter}}

        try:
            raw_results = collection.query(
                query_embeddings=query_vector.tolist(),
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.debug(
                "ChromaDB query failed for channel '%s': %s",
                channel.channel_name,
                e,
            )
            return []

        # Extract results (ChromaDB returns lists of lists)
        documents = raw_results.get("documents", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        distances = raw_results.get("distances", [[]])[0]

        if not documents:
            return []

        # Build results with score boosting
        results: List[RetrievalResult] = []
        for doc_text, meta, distance in zip(documents, metadatas, distances):
            # ChromaDB returns cosine distance (0 = identical, 1 = orthogonal)
            # Convert to similarity score
            base_score = 1.0 - float(distance)
            final_score = self._apply_tag_boost(
                base_score, meta, channel.tags_filter
            )

            chunk_id = meta.get("chunk_id", meta.get("doc_id", "unknown"))
            results.append(
                RetrievalResult(
                    chunk_id=chunk_id,
                    text=doc_text,
                    score=final_score,
                    metadata=meta,
                    channel=channel.channel_name,
                )
            )

        # Sort by boosted score and take top-k
        results.sort(key=lambda r: r.score, reverse=True)
        return results[: channel.k]

    # ── Internal: Metadata Score Boosting ────────────────────

    @staticmethod
    def _apply_tag_boost(
        base_score: float,
        metadata: Dict[str, Any],
        tags_filter: Optional[List[str]],
    ) -> float:
        """
        Boost the score if the chunk's tags match the query's tags_filter.

        The boost is additive: +0.05 for each matching tag.
        This prefers relevant chunks without excluding non-matching ones.
        """
        if not tags_filter:
            return base_score

        # ChromaDB stores tags as comma-separated strings
        chunk_tags_str = metadata.get("tags", "")
        if not chunk_tags_str:
            return base_score

        chunk_tags = set(chunk_tags_str.split(","))
        matched = sum(1 for tag in tags_filter if tag in chunk_tags)

        if matched > 0:
            boost = 0.05 * matched
            return min(base_score + boost, 1.0)

        return base_score

    # ── Internal: Collection Access ──────────────────────────

    def _get_collection(self) -> Any:
        """Lazy-load the ChromaDB collection."""
        if self._collection is not None:
            return self._collection

        try:
            self._collection = self.indexer.load()
        except Exception as e:
            logger.warning("Failed to load ChromaDB collection: %s", e)
            raise
        return self._collection


# ──────────────────────────────────────────────────────────────
# Factory
# ──────────────────────────────────────────────────────────────


def build_default_retriever(
    chroma_dir: Optional[str] = None,
    knowledge_dir: Optional[str] = None,
) -> Optional[Retriever]:
    """
    Build a Retriever with default paths, or return None if unavailable.

    This factory is designed for the lifespan startup — it returns None
    (rather than raising) when the index doesn't exist yet, so the
    application can degrade gracefully.

    Usage::

        retriever = build_default_retriever()
        # retriever may be None if the index hasn't been built
    """
    from .indexer import get_indexer

    try:
        embedder = Embedder()
        indexer = get_indexer(
            chroma_dir=chroma_dir,
            knowledge_dir=knowledge_dir,
            embedder=embedder,
        )

        if not indexer.index_exists():
            logger.info(
                "ChromaDB index not found at %s. "
                "Run `python scripts/build_kb_index.py` to create it. "
                "Retrieval will be disabled until then.",
                indexer.chroma_dir,
            )
            return None

        retriever = Retriever(indexer=indexer, embedder=embedder)
        # Force collection load to verify it works at startup
        retriever.is_available()
        logger.info("Retriever initialized successfully")
        return retriever

    except ImportError as e:
        logger.warning(
            "Retrieval dependencies not installed: %s. "
            "Install with: pip install chromadb sentence-transformers",
            e,
        )
        return None
    except Exception as e:
        logger.warning("Retriever initialization failed: %s", e)
        return None