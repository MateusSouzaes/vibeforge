"""Search engine service using vector embeddings and semantic search."""

import time
import hashlib
from typing import List, Optional, Dict, Tuple
from collections import defaultdict
from src.rag.models import (
    QueryType,
    ContentSource,
    QueryRequest,
    QueryContext,
    RankedResult,
    SearchResult,
    SearchStats,
    SearchConfig,
)
from src.embeddings.vector_index import VectorIndex
from src.embeddings.models import EmbeddingSource


class SearchCache:
    """Simple in-memory cache for search results."""

    def __init__(self, ttl_seconds: int = 3600):
        """Initialize cache.
        
        Args:
            ttl_seconds: Time-to-live for cached items
        """
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[SearchResult, float]] = {}

    def get(self, query_hash: str) -> Optional[SearchResult]:
        """Get cached result if not expired.
        
        Args:
            query_hash: Hash of the query
            
        Returns:
            Cached SearchResult or None if expired/missing
        """
        if query_hash not in self.cache:
            return None
        
        result, timestamp = self.cache[query_hash]
        if time.time() - timestamp > self.ttl_seconds:
            del self.cache[query_hash]
            return None
        
        return result

    def set(self, query_hash: str, result: SearchResult):
        """Cache a search result.
        
        Args:
            query_hash: Hash of the query
            result: SearchResult to cache
        """
        self.cache[query_hash] = (result, time.time())

    def clear(self):
        """Clear all cached items."""
        self.cache.clear()


class SearchService:
    """Semantic search service using vector embeddings."""

    def __init__(
        self,
        vector_index: VectorIndex,
        config: Optional[SearchConfig] = None
    ):
        """Initialize search service.
        
        Args:
            vector_index: VectorIndex instance for search
            config: SearchConfig for behavior customization
        """
        self.vector_index = vector_index
        self.config = config or SearchConfig()
        self.config.validate()
        
        self.cache = SearchCache(self.config.cache_ttl_seconds) if self.config.use_caching else None
        self.stats = SearchStats()
        self.query_history: List[QueryRequest] = []

    def search(self, query: QueryRequest) -> SearchResult:
        """Execute a semantic search.
        
        Args:
            query: QueryRequest with search parameters
            
        Returns:
            SearchResult with ranked results
        """
        start_time = time.time()
        
        # Check cache
        query_hash = self._hash_query(query)
        if self.cache:
            cached = self.cache.get(query_hash)
            if cached:
                return cached
        
        try:
            # Perform search
            sim_result = self.vector_index.search(
                query.query_text,
                top_k=query.context.max_results,
                threshold=query.context.min_score
            )
            
            # Convert to ranked results
            ranked_results = self._rank_results(
                sim_result.results,
                query.context
            )
            
            # Create search result
            result = SearchResult(
                query_id=query.query_id,
                query_text=query.query_text,
                query_type=query.context.query_type,
                results=ranked_results,
                total_results_found=len(ranked_results),
                search_time_ms=(time.time() - start_time) * 1000,
                model_used=self.config.embedding_model
            )
            
            # Cache result
            if self.cache:
                self.cache.set(query_hash, result)
            
            # Update stats
            self._update_stats(result, success=True)
            self.query_history.append(query)
            
            return result
            
        except Exception as e:
            self.stats.failed_searches += 1
            raise

    def search_by_type(
        self,
        query_text: str,
        query_type: QueryType = QueryType.SEMANTIC,
        **kwargs
    ) -> SearchResult:
        """Search with specific query type.
        
        Args:
            query_text: Text to search
            query_type: Type of query
            **kwargs: Additional context parameters
            
        Returns:
            SearchResult
        """
        context = QueryContext(
            query_type=query_type,
            **kwargs
        )
        query = QueryRequest(query_text, context=context)
        return self.search(query)

    def semantic_search(
        self,
        query_text: str,
        max_results: int = 10,
        min_score: float = 0.5
    ) -> SearchResult:
        """Perform semantic search (convenience method).
        
        Args:
            query_text: Text to search
            max_results: Maximum results
            min_score: Minimum similarity score
            
        Returns:
            SearchResult
        """
        context = QueryContext(
            query_type=QueryType.SEMANTIC,
            max_results=max_results,
            min_score=min_score
        )
        query = QueryRequest(query_text, context=context)
        return self.search(query)

    def code_search(
        self,
        query_text: str,
        language: Optional[str] = None,
        max_results: int = 10
    ) -> SearchResult:
        """Search for code patterns.
        
        Args:
            query_text: Code pattern to search
            language: Programming language filter
            max_results: Maximum results
            
        Returns:
            SearchResult
        """
        context = QueryContext(
            query_type=QueryType.CODE_PATTERN,
            language=language,
            source_type=ContentSource.CODE,
            max_results=max_results
        )
        query = QueryRequest(query_text, context=context)
        return self.search(query)

    def decision_search(
        self,
        query_text: str,
        max_results: int = 10
    ) -> SearchResult:
        """Search for architectural decisions.
        
        Args:
            query_text: Decision topic to search
            max_results: Maximum results
            
        Returns:
            SearchResult
        """
        context = QueryContext(
            query_type=QueryType.DECISION,
            source_type=ContentSource.ARCHITECTURAL_DECISION,
            max_results=max_results
        )
        query = QueryRequest(query_text, context=context)
        return self.search(query)

    def _rank_results(
        self,
        results: List[Dict],
        context: QueryContext
    ) -> List[RankedResult]:
        """Convert and rank search results.
        
        Args:
            results: Raw search results from vector index
            context: Query context for filtering
            
        Returns:
            Ranked results
        """
        ranked = []
        
        for rank, result in enumerate(results, 1):
            # Filter by criteria
            if context.source_type and result.get("source_type") != context.source_type.value:
                continue
            
            if context.repository and result.get("file_path", "").find(context.repository) == -1:
                continue
            
            # Create ranked result
            ranked_result = RankedResult(
                document_id=result.get("document_id", f"doc_{rank}"),
                title=result.get("title", "Untitled"),
                content=result.get("content_preview", ""),
                source_type=self._parse_source_type(result.get("source_type", "code")),
                similarity_score=result.get("similarity_score", 0.0),
                rank=rank,
                file_path=result.get("file_path"),
                repository=result.get("repository"),
                tags=result.get("tags", [])
            )
            ranked.append(ranked_result)
        
        # Re-rank if configured
        if self.config.use_reranking and len(ranked) > 1:
            ranked = self._rerank_results(ranked, context)
        
        return ranked

    def _rerank_results(
        self,
        results: List[RankedResult],
        context: QueryContext
    ) -> List[RankedResult]:
        """Re-rank results using additional signals.
        
        Args:
            results: Initial ranked results
            context: Query context
            
        Returns:
            Re-ranked results
        """
        # Boost scores based on type and source
        for result in results:
            boost = 1.0
            
            # Boost by type match
            if context.query_type == QueryType.CODE_PATTERN:
                if result.source_type == ContentSource.CODE:
                    boost *= 1.2
            elif context.query_type == QueryType.DECISION:
                if result.source_type == ContentSource.ARCHITECTURAL_DECISION:
                    boost *= 1.3
            
            # Boost by recency (simplified)
            boost *= 0.95  # Slight decay
            
            result.similarity_score = min(1.0, result.similarity_score * boost)
        
        # Re-sort by boosted scores
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Update ranks
        for i, result in enumerate(results, 1):
            result.rank = i
        
        return results

    def get_stats(self) -> SearchStats:
        """Get search statistics.
        
        Returns:
            SearchStats
        """
        if self.stats.total_searches > 0:
            self.stats.average_results_returned = (
                sum(q.context.max_results if hasattr(q.context, 'max_results') else 0 
                    for q in self.query_history) / len(self.query_history)
            )
        
        return self.stats

    def clear_cache(self):
        """Clear search cache."""
        if self.cache:
            self.cache.clear()

    def _hash_query(self, query: QueryRequest) -> str:
        """Generate hash for query caching.
        
        Args:
            query: QueryRequest
            
        Returns:
            Query hash
        """
        query_str = f"{query.query_text}:{query.context.query_type.value}"
        return hashlib.md5(query_str.encode()).hexdigest()

    def _update_stats(self, result: SearchResult, success: bool = True):
        """Update search statistics.
        
        Args:
            result: SearchResult
            success: Whether search was successful
        """
        self.stats.total_searches += 1
        if success:
            self.stats.successful_searches += 1
        else:
            self.stats.failed_searches += 1

    def _parse_source_type(self, source_str: str) -> ContentSource:
        """Parse source type string.
        
        Args:
            source_str: Source type string
            
        Returns:
            ContentSource enum
        """
        try:
            return ContentSource(source_str.lower())
        except ValueError:
            return ContentSource.CODE

    def get_query_history(self, limit: int = 10) -> List[QueryRequest]:
        """Get recent query history.
        
        Args:
            limit: Maximum queries to return
            
        Returns:
            List of recent queries
        """
        return self.query_history[-limit:]

    def get_popular_searches(self, top_n: int = 5) -> List[Tuple[str, int]]:
        """Get most popular search queries.
        
        Args:
            top_n: Number of top searches to return
            
        Returns:
            List of (query_text, count) tuples
        """
        query_counts: Dict[str, int] = defaultdict(int)
        for query in self.query_history:
            query_counts[query.query_text] += 1
        
        sorted_queries = sorted(
            query_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_queries[:top_n]
