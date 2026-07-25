"""
services/retrieval/embedder.py

Wraps a Sentence Transformers model for generating embeddings.
Uses a lightweight model (all-MiniLM-L6-v2) suitable for CPU inference.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Any

import numpy as np

logger = logging.getLogger(__name__)

# Default embedding model — lightweight, 384-dim, fast on CPU
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_EMBEDDING_DIMENSION = 384


class Embedder:
    """
    Generates embeddings for text chunks using Sentence Transformers.

    The model is loaded lazily on first use to avoid blocking imports.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        device: Optional[str] = None,
    ):
        """
        Args:
            model_name: Name of the Sentence Transformers model.
            device: Override device (e.g., "cpu", "cuda"). If None, auto-detect.
        """
        self.model_name = model_name
        self._device = device
        self._model: Any = None
        # Dimension may be unknown until model is loaded; allow None for typing
        self._dimension: Optional[int] = DEFAULT_EMBEDDING_DIMENSION

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        # Ensure we have a concrete int dimension. Load model if needed.
        if self._dimension is None:
            # this will load the model and populate _dimension
            _ = self.model
        # mypy/type checkers may still consider _dimension Optional[int]; assert to narrow
        assert self._dimension is not None
        return int(self._dimension)

    @property
    def model(self) -> Any:
        """Lazy-load the Sentence Transformers model."""
        if self._model is None:
            self._load_model()
        return self._model

    def _load_model(self) -> None:
        """Load the Sentence Transformers model (called once on first use)."""
        logger.info(
            "Loading embedding model: %s (this may download ~80 MB on first run)",
            self.model_name,
        )
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers is required. "
                "Install it with: pip install sentence-transformers"
            )

        self._model = SentenceTransformer(
            self.model_name,
            device=self._device,
        )
        # SentenceTransformer renamed get_sentence_embedding_dimension -> get_embedding_dimension
        # The method may return Optional[int], so coerce to int safely.
        try:
            dim = getattr(self._model, "get_embedding_dimension")()
        except AttributeError:
            dim = getattr(self._model, "get_sentence_embedding_dimension")()
        self._dimension = int(dim) if dim is not None else DEFAULT_EMBEDDING_DIMENSION
        logger.info(
            "Embedding model loaded: %s (dim=%d, device=%s)",
            self.model_name,
            self._dimension,
            self._model.device,
        )

    def embed(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of text strings.

        Args:
            texts: List of text strings to embed.

        Returns:
            numpy array of shape (len(texts), dimension).
        """
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        model = self.model
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=32,
        )
        return embeddings.astype(np.float32)

    def embed_single(self, text: str) -> np.ndarray:
        """Embed a single text string. Returns shape (dimension,)."""
        return self.embed([text])[0]