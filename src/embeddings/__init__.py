"""Embeddings module for generating and managing vector embeddings."""

from src.embeddings.models import (
    EmbeddingSource,
    EmbeddingVector,
    EmbeddingBatch,
    IndexedDocument,
    SimilarityResult,
    VectorIndexStats,
)
from src.embeddings.embedding_generator import EmbeddingGenerator
from src.embeddings.vector_index import VectorIndex

__all__ = [
    "EmbeddingSource",
    "EmbeddingVector",
    "EmbeddingBatch",
    "IndexedDocument",
    "SimilarityResult",
    "VectorIndexStats",
    "EmbeddingGenerator",
    "VectorIndex",
]
