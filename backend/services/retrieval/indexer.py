"""
services/retrieval/indexer.py

Builds and manages a persistent ChromaDB vector index from knowledge chunks.
Supports creating new indexes, updating existing ones, and runtime loading.
"""

from __future__ import annotations

import os
import time
import logging
from typing import List, Optional

import chromadb.config
import chromadb.config
import numpy as np

from .chunk_loader import KnowledgeChunk, ChunkLoader
from .embedder import Embedder

logger = logging.getLogger(__name__)

# Default persistent ChromaDB location
DEFAULT_CHROMA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "data", "chroma",
)

# Default knowledge base directory
DEFAULT_KNOWLEDGE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "data", "knowledge",
)

# Collection name inside ChromaDB
COLLECTION_NAME = "resilienceai_knowledge"


class Indexer:
    """
    Builds and manages a persistent ChromaDB vector index.
    
    Usage:
        indexer = Indexer()
        indexer.build()         # Build from knowledge base
        indexer.load()          # Load existing index for queries
    """

    def __init__(
        self,
        chroma_dir: str = DEFAULT_CHROMA_DIR,
        knowledge_dir: str = DEFAULT_KNOWLEDGE_DIR,
        embedder: Optional[Embedder] = None,
        collection_name: str = COLLECTION_NAME,
    ):
        self.chroma_dir = os.path.abspath(chroma_dir)
        self.knowledge_dir = os.path.abspath(knowledge_dir)
        self.collection_name = collection_name

        if embedder is not None:
            self.embedder = embedder
        else:
            self.embedder = Embedder()

        self._client = None
        self._collection = None

    # ──────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────

    def build(self) -> int:
        """
        Build (or rebuild) the ChromaDB index from the knowledge base.
        
        Returns:
            Number of chunks indexed.
        
        Raises:
            ValueError: If knowledge documents fail validation.
        """
        logger.info("=" * 60)
        logger.info("BUILDING KNOWLEDGE BASE VECTOR INDEX")
        logger.info("=" * 60)
        logger.info("Embedding model: %s", self.embedder.model_name)
        logger.info("Knowledge base:  %s", self.knowledge_dir)
        logger.info("ChromaDB dir:    %s", self.chroma_dir)
        logger.info("Collection:      %s", self.collection_name)

        start_time = time.time()

        # 1. Load and validate all knowledge documents
        loader = ChunkLoader(self.knowledge_dir)
        chunks = loader.load_all()
        logger.info(
            "Documents processed: %d (using virtual doc count from chunks)",
            len({c.doc_id for c in chunks}),
        )
        logger.info("Chunks created:     %d", len(chunks))

        if not chunks:
            logger.warning("No chunks to index. Aborting build.")
            return 0

        # 2. Generate embeddings
        logger.info("Generating embeddings for %d chunks...", len(chunks))
        texts = [c.text for c in chunks]
        embeddings = self.embedder.embed(texts)
        logger.info(
            "Embeddings generated: shape=%s, dim=%d",
            embeddings.shape,
            self.embedder.dimension,
        )

        # 3. Build ChromaDB index
        client = self._get_client()
        collection = self._get_or_create_collection(client)

        # Build metadata + IDs
        ids = [c.chunk_id for c in chunks]
        metadatas = []
        for c in chunks:
            meta = {
                "doc_id": c.doc_id,
                "category": c.category,
                "tags": ",".join(c.tags),
                "title": c.title,
                "chunk_index": c.chunk_index,
                "total_chunks": c.total_chunks,
                "source_title": c.source_title,
                "source_org": c.source_org,
                "source_url": c.source_url,
                "source_license": c.source_license or "",
            }
            # Add any extra metadata from applies_when etc.
            for key, value in c.metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    meta[f"meta_{key}"] = value
                else:
                    meta[f"meta_{key}"] = str(value)
            metadatas.append(meta)

        # Delete existing data in this collection to avoid duplicates
        existing_count = collection.count()
        if existing_count > 0:
            logger.info(
                "Collection already contains %d records. Replacing...",
                existing_count,
            )
            collection.delete(collection.get()["ids"])

        # Upsert
        collection.add(
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )

        elapsed = time.time() - start_time
        final_count = collection.count()
        logger.info("-" * 60)
        logger.info("INDEX BUILD COMPLETE")
        logger.info("  Total chunks indexed:  %d", final_count)
        logger.info("  Processing duration:   %.2f seconds", elapsed)
        logger.info("  ChromaDB location:     %s", self.chroma_dir)
        logger.info("  Collection name:       %s", self.collection_name)
        logger.info("=" * 60)

        return final_count

    def load(self):
        """
        Load an existing ChromaDB index for querying.
        
        Returns:
            The ChromaDB collection object.
        
        Raises:
            FileNotFoundError: If the ChromaDB directory does not exist.
            RuntimeError: If the collection is missing or empty.
        """
        if not os.path.exists(self.chroma_dir):
            raise FileNotFoundError(
                f"ChromaDB index not found at: {self.chroma_dir}. "
                "Run build_index.py first to create the index."
            )

        client = self._get_client()
        try:
            collection = client.get_collection(self.collection_name)
        except Exception as e:
            # ChromaDB raises NotFoundError when collection doesn't exist
            raise FileNotFoundError(
                f"ChromaDB collection '{self.collection_name}' not found "
                f"in {self.chroma_dir}. Run build_index.py to create it."
            ) from e

        count = collection.count()
        if count == 0:
            raise RuntimeError(
                f"ChromaDB collection '{self.collection_name}' is empty. "
                "Run build_index.py to rebuild the index."
            )

        self._collection = collection
        logger.info(
            "Loaded ChromaDB index: %d records, collection='%s'",
            count,
            self.collection_name,
        )
        return collection

    def index_exists(self) -> bool:
        """
        Check whether a valid ChromaDB index exists at the configured path.
        
        Returns:
            True if the index exists and contains records, False otherwise.
        """
        if not os.path.exists(self.chroma_dir):
            return False

        try:
            client = self._get_client()
            collection = client.get_collection(self.collection_name)
            return collection.count() > 0
        except (ValueError, RuntimeError):
            return False
        except Exception:
            # Catch chromadb.errors.NotFoundError (not importable at module level)
            return False

    # ──────────────────────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────────────────────

    def _get_client(self):
        """Get or create the ChromaDB persistent client."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
            except ImportError:
                raise ImportError(
                    "chromadb is required. Install it with: pip install chromadb"
                )

            # Ensure the directory exists
            os.makedirs(self.chroma_dir, exist_ok=True)

            self._client = chromadb.PersistentClient(
                path=self.chroma_dir,
                settings=Settings(
                    anonymized_telemetry=False,
                ),
            )
            logger.debug("ChromaDB persistent client initialized at %s", self.chroma_dir)

        return self._client

    def _get_or_create_collection(self, client):
        """Get an existing collection or create a new one."""
        try:
            collection = client.get_collection(self.collection_name)
            logger.debug(
                "Using existing collection '%s' (%d records)",
                self.collection_name,
                collection.count(),
            )
        except Exception:
            collection = client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.debug(
                "Created new collection '%s'",
                self.collection_name,
            )
        return collection


def get_indexer(
    chroma_dir: Optional[str] = None,
    knowledge_dir: Optional[str] = None,
    embedder: Optional[Embedder] = None,
) -> Indexer:
    """
    Convenience factory function for creating an Indexer with default paths.
    
    Args:
        chroma_dir: Override default ChromaDB directory.
        knowledge_dir: Override default knowledge base directory.
        embedder: Override default Embedder.
    
    Returns:
        Configured Indexer instance.
    """
    return Indexer(
        chroma_dir=chroma_dir or DEFAULT_CHROMA_DIR,
        knowledge_dir=knowledge_dir or DEFAULT_KNOWLEDGE_DIR,
        embedder=embedder,
    )