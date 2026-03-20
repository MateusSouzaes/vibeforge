"""Data models for RAG (Retrieval-Augmented Generation) search engine."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class QueryType(Enum):
    """Types of queries supported by the search engine."""
    
    SEMANTIC = "semantic"  # Natural language semantic search
    CODE_PATTERN = "code_pattern"  # Search for code patterns
    ARCHITECTURE = "architecture"  # Architectural decisions
    DECISION = "decision"  # Decision search
    COMMIT = "commit"  # Commit history search
    DOCUMENTATION = "documentation"  # Documentation search
    HYBRID = "hybrid"  # Combination of multiple types


class ContentSource(Enum):
    """Source of the content being searched."""
    
    CODE = "code"
    DOCUMENTATION = "documentation"
    COMMIT_MESSAGE = "commit_message"
    ARCHITECTURAL_DECISION = "architectural_decision"
    PATTERN = "pattern"


@dataclass
class QueryContext:
    """Context information for a query."""
    
    query_type: QueryType
    language: Optional[str] = None  # Programming language filter
    repository: Optional[str] = None  # Repository filter
    source_type: Optional[ContentSource] = None  # Source type filter
    time_range: Optional[tuple] = None  # (start_date, end_date)
    min_score: float = 0.5  # Minimum similarity score
    max_results: int = 10  # Maximum results to return
    
    def __post_init__(self):
        if not (0.0 <= self.min_score <= 1.0):
            raise ValueError("min_score must be between 0.0 and 1.0")
        if self.max_results < 1:
            raise ValueError("max_results must be at least 1")


@dataclass
class QueryRequest:
    """Request for semantic search."""
    
    query_text: str
    query_id: str = field(default_factory=lambda: f"query_{datetime.now().timestamp()}")
    context: QueryContext = field(default_factory=lambda: QueryContext(QueryType.SEMANTIC))
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.query_text or not self.query_text.strip():
            raise ValueError("query_text cannot be empty")
        if len(self.query_text) > 2000:
            raise ValueError("query_text cannot exceed 2000 characters")


@dataclass
class RankedResult:
    """A single ranked search result."""
    
    document_id: str
    title: str
    content: str
    source_type: ContentSource
    similarity_score: float
    rank: int
    file_path: Optional[str] = None
    repository: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    matched_keywords: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not (0.0 <= self.similarity_score <= 1.0):
            raise ValueError("similarity_score must be between 0.0 and 1.0")
        if self.rank < 1:
            raise ValueError("rank must be at least 1")


@dataclass
class SearchResult:
    """Result of a search query with ranked results."""
    
    query_id: str
    query_text: str
    query_type: QueryType
    results: List[RankedResult] = field(default_factory=list)
    total_results_found: int = 0
    search_time_ms: float = 0.0
    model_used: str = "semantic-search"
    executed_at: datetime = field(default_factory=datetime.now)
    
    @property
    def has_results(self) -> bool:
        """Check if search found any results."""
        return len(self.results) > 0
    
    @property
    def average_score(self) -> float:
        """Calculate average similarity score."""
        if not self.results:
            return 0.0
        return sum(r.similarity_score for r in self.results) / len(self.results)
    
    @property
    def top_result(self) -> Optional[RankedResult]:
        """Get the best result."""
        return self.results[0] if self.results else None


@dataclass
class SearchStats:
    """Statistics about searches performed."""
    
    total_searches: int = 0
    successful_searches: int = 0
    failed_searches: int = 0
    average_results_returned: float = 0.0
    average_search_time_ms: float = 0.0
    most_common_query_type: Optional[QueryType] = None
    unique_users: int = 0
    date_collected: datetime = field(default_factory=datetime.now)
    
    def add_search(self, result: SearchResult, success: bool = True):
        """Record a search in statistics."""
        self.total_searches += 1
        if success:
            self.successful_searches += 1
        else:
            self.failed_searches += 1


@dataclass
class SearchFilter:
    """Advanced search filters."""
    
    by_source: Optional[List[ContentSource]] = None
    by_repository: Optional[List[str]] = None
    by_language: Optional[List[str]] = None
    by_date_range: Optional[tuple] = None  # (start_date, end_date)
    exclude_keywords: List[str] = field(default_factory=list)
    include_keywords: List[str] = field(default_factory=list)
    min_length: int = 0  # Minimum content length
    max_length: Optional[int] = None  # Maximum content length


@dataclass
class SearchConfig:
    """Configuration for search behavior."""
    
    embedding_model: str = "semantic-search"
    similarity_threshold: float = 0.5
    max_results: int = 20
    timeout_seconds: float = 30.0
    use_reranking: bool = True  # Re-rank results using LLM
    use_caching: bool = True  # Cache search results
    cache_ttl_seconds: int = 3600  # Cache time-to-live
    enable_analytics: bool = True  # Track search analytics
    
    def validate(self):
        """Validate configuration."""
        if not (0.0 <= self.similarity_threshold <= 1.0):
            raise ValueError("similarity_threshold must be 0.0-1.0")
        if self.max_results < 1:
            raise ValueError("max_results must be >= 1")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        if self.cache_ttl_seconds < 0:
            raise ValueError("cache_ttl_seconds must be >= 0")
