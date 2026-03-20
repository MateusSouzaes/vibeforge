"""Tests for RAG search service module."""

import pytest
from datetime import datetime
from src.rag.search_service import SearchService, SearchCache
from src.rag.models import (
    QueryType,
    ContentSource,
    QueryRequest,
    QueryContext,
    RankedResult,
    SearchResult,
    SearchConfig,
)
from src.embeddings.vector_index import VectorIndex
from src.embeddings.models import IndexedDocument, EmbeddingSource


class TestSearchCache:
    """Test SearchCache functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cache = SearchCache(ttl_seconds=100)

    def test_cache_initialization(self):
        """Test cache initialization."""
        assert self.cache.ttl_seconds == 100
        assert len(self.cache.cache) == 0

    def test_set_and_get(self):
        """Test storing and retrieving from cache."""
        result = SearchResult(
            query_id="q1",
            query_text="test query",
            query_type=QueryType.SEMANTIC
        )
        
        self.cache.set("hash1", result)
        cached = self.cache.get("hash1")
        
        assert cached is not None
        assert cached.query_text == "test query"

    def test_get_nonexistent(self):
        """Test getting non-existent cache entry."""
        cached = self.cache.get("nonexistent")
        assert cached is None

    def test_cache_expiration(self):
        """Test cache TTL expiration."""
        cache_short = SearchCache(ttl_seconds=0)
        result = SearchResult(
            query_id="q1",
            query_text="test",
            query_type=QueryType.SEMANTIC
        )
        
        cache_short.set("hash1", result)
        
        # Wait for expiration
        import time
        time.sleep(0.1)
        
        cached = cache_short.get("hash1")
        assert cached is None

    def test_clear_cache(self):
        """Test clearing cache."""
        result = SearchResult(
            query_id="q1",
            query_text="test",
            query_type=QueryType.SEMANTIC
        )
        
        self.cache.set("hash1", result)
        self.cache.clear()
        
        assert len(self.cache.cache) == 0


class TestSearchService:
    """Test SearchService functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.vector_index = VectorIndex(embedding_dim=128)
        self.search_service = SearchService(self.vector_index)
        
        # Add sample documents
        self.doc1 = IndexedDocument(
            document_id="doc1",
            title="Python Best Practices",
            content="Use type hints and follow PEP 8 standards",
            source_type=EmbeddingSource.DOCUMENTATION,
            vector_id="vec1",
            repository="test-repo",
        )
        self.doc2 = IndexedDocument(
            document_id="doc2",
            title="Architecture Decision",
            content="We decided to use microservices architecture",
            source_type=EmbeddingSource.DECISION,
            vector_id="vec2",
            repository="test-repo",
        )
        
        self.vector_index.add_document(self.doc1)
        self.vector_index.add_document(self.doc2)

    def test_service_initialization(self):
        """Test SearchService initialization."""
        assert self.search_service.vector_index is not None
        assert self.search_service.config is not None
        assert self.search_service.cache is not None

    def test_service_with_custom_config(self):
        """Test SearchService with custom config."""
        config = SearchConfig(
            max_results=5,
            similarity_threshold=0.7,
            use_caching=False
        )
        service = SearchService(self.vector_index, config)
        
        assert service.config.max_results == 5
        assert service.config.use_caching is False
        assert service.cache is None

    def test_semantic_search(self):
        """Test semantic search."""
        result = self.search_service.semantic_search("Python standards")
        
        assert isinstance(result, SearchResult)
        assert result.query_type == QueryType.SEMANTIC
        assert result.search_time_ms > 0

    def test_code_search(self):
        """Test code pattern search."""
        result = self.search_service.code_search("type hints")
        
        assert result.query_type == QueryType.CODE_PATTERN
        assert result.total_results_found >= 0

    def test_decision_search(self):
        """Test decision search."""
        result = self.search_service.decision_search("architecture")
        
        assert result.query_type == QueryType.DECISION
        assert result.total_results_found >= 0

    def test_search_with_context(self):
        """Test search with custom context."""
        context = QueryContext(
            query_type=QueryType.SEMANTIC,
            max_results=5,
            min_score=0.3
        )
        query = QueryRequest("Python", context=context)
        result = self.search_service.search(query)
        
        assert result.total_results_found <= 5

    def test_search_result_has_results(self):
        """Test SearchResult.has_results property."""
        result = SearchResult(
            query_id="q1",
            query_text="test",
            query_type=QueryType.SEMANTIC
        )
        
        assert result.has_results is False
        
        result.results.append(
            RankedResult(
                document_id="doc1",
                title="Test",
                content="test content",
                source_type=ContentSource.CODE,
                similarity_score=0.9,
                rank=1
            )
        )
        
        assert result.has_results is True

    def test_search_result_average_score(self):
        """Test SearchResult.average_score calculation."""
        result = SearchResult(
            query_id="q1",
            query_text="test",
            query_type=QueryType.SEMANTIC
        )
        
        result.results.append(
            RankedResult(
                document_id="doc1",
                title="Test 1",
                content="content",
                source_type=ContentSource.CODE,
                similarity_score=0.8,
                rank=1
            )
        )
        result.results.append(
            RankedResult(
                document_id="doc2",
                title="Test 2",
                content="content",
                source_type=ContentSource.CODE,
                similarity_score=0.6,
                rank=2
            )
        )
        
        assert result.average_score == 0.7

    def test_search_result_top_result(self):
        """Test SearchResult.top_result property."""
        result = SearchResult(
            query_id="q1",
            query_text="test",
            query_type=QueryType.SEMANTIC
        )
        
        assert result.top_result is None
        
        ranked = RankedResult(
            document_id="doc1",
            title="Top",
            content="content",
            source_type=ContentSource.CODE,
            similarity_score=0.95,
            rank=1
        )
        result.results.append(ranked)
        
        assert result.top_result is ranked

    def test_caching_behavior(self):
        """Test that caching works correctly."""
        result1 = self.search_service.semantic_search("Python")
        result2 = self.search_service.semantic_search("Python")
        
        # Both should be SearchResult objects
        assert isinstance(result1, SearchResult)
        assert isinstance(result2, SearchResult)

    def test_cache_clear(self):
        """Test clearing cache."""
        self.search_service.semantic_search("Python")
        
        assert len(self.search_service.cache.cache) > 0
        
        self.search_service.clear_cache()
        
        assert len(self.search_service.cache.cache) == 0

    def test_get_stats(self):
        """Test retrieving search statistics."""
        self.search_service.semantic_search("Python")
        self.search_service.semantic_search("architecture")
        
        stats = self.search_service.get_stats()
        
        assert stats.total_searches >= 2
        assert stats.successful_searches >= 2

    def test_query_history(self):
        """Test query history tracking."""
        self.search_service.semantic_search("Python")
        self.search_service.code_search("def")
        
        history = self.search_service.get_query_history(limit=10)
        
        assert len(history) >= 2

    def test_query_history_limit(self):
        """Test query history limit."""
        for i in range(15):
            self.search_service.semantic_search(f"query {i}")
        
        history = self.search_service.get_query_history(limit=5)
        
        assert len(history) == 5

    def test_popular_searches(self):
        """Test finding popular searches."""
        self.search_service.semantic_search("Python")
        self.search_service.semantic_search("Python")
        self.search_service.semantic_search("patterns")
        
        popular = self.search_service.get_popular_searches(top_n=1)
        
        assert len(popular) >= 1
        assert popular[0][0] == "Python"

    def test_search_by_type(self):
        """Test search_by_type convenience method."""
        result = self.search_service.search_by_type(
            "architecture",
            query_type=QueryType.DECISION
        )
        
        assert result.query_type == QueryType.DECISION

    def test_query_request_validation(self):
        """Test QueryRequest validation."""
        with pytest.raises(ValueError):
            QueryRequest("")  # Empty query
        
        with pytest.raises(ValueError):
            QueryRequest("x" * 2001)  # Too long

    def test_query_context_validation(self):
        """Test QueryContext validation."""
        with pytest.raises(ValueError):
            QueryContext(
                query_type=QueryType.SEMANTIC,
                min_score=1.5  # Invalid score
            )
        
        with pytest.raises(ValueError):
            QueryContext(
                query_type=QueryType.SEMANTIC,
                max_results=0  # Invalid max_results
            )

    def test_search_config_validation(self):
        """Test SearchConfig validation."""
        with pytest.raises(ValueError):
            config = SearchConfig(similarity_threshold=1.5)
            config.validate()
        
        with pytest.raises(ValueError):
            config = SearchConfig(timeout_seconds=-1)
            config.validate()

    def test_ranked_result_validation(self):
        """Test RankedResult validation."""
        with pytest.raises(ValueError):
            RankedResult(
                document_id="doc",
                title="test",
                content="content",
                source_type=ContentSource.CODE,
                similarity_score=1.5,  # Invalid score
                rank=1
            )
        
        with pytest.raises(ValueError):
            RankedResult(
                document_id="doc",
                title="test",
                content="content",
                source_type=ContentSource.CODE,
                similarity_score=0.8,
                rank=0  # Invalid rank
            )

    def test_multiple_search_types(self):
        """Test different search types sequentially."""
        results_semantic = self.search_service.semantic_search("test")
        results_code = self.search_service.code_search("def")
        results_decision = self.search_service.decision_search("architecture")
        
        assert results_semantic.query_type == QueryType.SEMANTIC
        assert results_code.query_type == QueryType.CODE_PATTERN
        assert results_decision.query_type == QueryType.DECISION

    def test_search_with_max_results(self):
        """Test search respects max_results."""
        result = self.search_service.semantic_search(
            "Python",
            max_results=1
        )
        
        assert result.total_results_found <= 1

    def test_search_with_min_score(self):
        """Test search respects min_score threshold."""
        result_high = self.search_service.semantic_search(
            "xyz",
            min_score=0.9
        )
        result_low = self.search_service.semantic_search(
            "xyz",
            min_score=0.1
        )
        
        # Low threshold should return more or equal results
        assert result_low.total_results_found >= result_high.total_results_found

    def test_search_timestamps(self):
        """Test search result timestamps."""
        result = self.search_service.semantic_search("test")
        
        assert result.executed_at is not None
        assert isinstance(result.executed_at, datetime)

    def test_ranked_results_have_ranks(self):
        """Test that ranked results have sequential ranks."""
        doc_list = [
            IndexedDocument(
                document_id=f"doc{i}",
                title=f"Document {i}",
                content=f"Content {i}",
                source_type=EmbeddingSource.DOCUMENTATION,
                vector_id=f"vec{i}",
                repository="test-repo",
            )
            for i in range(3)
        ]
        
        index = VectorIndex(embedding_dim=128)
        for doc in doc_list:
            index.add_document(doc)
        
        service = SearchService(index)
        result = service.semantic_search("test", max_results=3)
        
        if result.results:
            ranks = [r.rank for r in result.results]
            assert ranks == sorted(ranks)  # Ranks should be sequential

    def test_search_result_model_field(self):
        """Test SearchResult.model_used field."""
        result = self.search_service.semantic_search("test")
        
        assert result.model_used == "semantic-search"

    def test_search_with_empty_index(self):
        """Test search on empty index."""
        empty_index = VectorIndex()
        service = SearchService(empty_index)
        
        result = service.semantic_search("anything")
        
        assert result.total_results_found == 0
        assert not result.has_results

    def test_content_source_parsing(self):
        """Test ContentSource parsing."""
        result = SearchResult(
            query_id="q1",
            query_text="test",
            query_type=QueryType.SEMANTIC
        )
        
        result.results.append(
            RankedResult(
                document_id="doc",
                title="test",
                content="content",
                source_type=ContentSource.CODE,
                similarity_score=0.8,
                rank=1
            )
        )
        
        assert result.results[0].source_type == ContentSource.CODE
