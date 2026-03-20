"""Data models for code embeddings and vector indexing."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict
from datetime import datetime


class EmbeddingSource(Enum):
    """Source of embedding content."""
    CODE = "code"
    DOCUMENTATION = "documentation"
    COMMIT_MESSAGE = "commit_message"
    DECISION = "decision"


@dataclass
class EmbeddingVector:
    """A single embedding vector with metadata."""
    content_id: str  # Unique ID for the content
    content: str  # Original content
    source: EmbeddingSource
    vector: List[float]  # Embedding vector
    dimensions: int  # Number of dimensions
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    similarity_score: float = 0.0  # For search results


@dataclass
class EmbeddingBatch:
    """Batch of embeddings to be indexed."""
    batch_id: str
    embeddings: List[EmbeddingVector]
    total_tokens: int = 0
    processing_time_ms: float = 0.0
    model_used: str = "text-embedding-default"
    batch_date: datetime = field(default_factory=datetime.now)


@dataclass
class IndexedDocument:
    """Document indexed in vector database."""
    document_id: str
    title: str
    content: str
    source_type: EmbeddingSource
    vector_id: str  # Reference to embedding
    repository: str
    file_path: Optional[str] = None
    line_range: Optional[tuple] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    indexed_at: datetime = field(default_factory=datetime.now)


@dataclass
class SimilarityResult:
    """Result of similarity search."""
    query_text: str
    results: List[Dict]  # [{document_id, title, similarity_score, content_preview}]
    query_embedding: Optional[List[float]] = None
    search_time_ms: float = 0.0
    threshold: float = 0.7  # Minimum similarity


@dataclass
class VectorIndexStats:
    """Statistics about vector index."""
    total_documents: int
    total_embeddings: int
    vector_dimensions: int
    index_size_mb: float
    last_updated: datetime
    sources_distribution: Dict[str, int]  # {source: count}
    coverage: Dict[str, float]  # {repository: percentage}
