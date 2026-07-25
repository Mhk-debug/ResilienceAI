"""
services/retrieval/__init__.py

Retrieval-augmented generation (RAG) package for ResilienceAI.
Provides chunk loading, embedding, ChromaDB vector indexing, query building,
and semantic retrieval.
"""

from .chunk_loader import KnowledgeChunk, ChunkLoader
from .embedder import Embedder
from .indexer import Indexer
from .query_builder import ChannelQuery, QueryBuilder
from .retriever import RetrievalResult, Retriever, build_default_retriever

__all__ = [
    "KnowledgeChunk",
    "ChunkLoader",
    "Embedder",
    "Indexer",
    "ChannelQuery",
    "QueryBuilder",
    "RetrievalResult",
    "Retriever",
    "build_default_retriever",
]
