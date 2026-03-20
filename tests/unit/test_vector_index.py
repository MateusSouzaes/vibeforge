"""Tests for vector index module."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from src.embeddings.vector_index import VectorIndex
from src.embeddings.models import IndexedDocument, EmbeddingSource


class TestVectorIndex:
    """Test VectorIndex class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.index = VectorIndex(embedding_dim=128)
        self.sample_doc1 = IndexedDocument(
            document_id="doc1",
            title="Test Document 1",
            content="This is the first test document about Python",
            source_type=EmbeddingSource.DOCUMENTATION,
            vector_id="vec1",
            file_path="/docs/test1.md",
            tags=["python", "testing"],
            repository="test-repo",
        )
        self.sample_doc2 = IndexedDocument(
            document_id="doc2",
            title="Test Document 2",
            content="This is the second test document about Python frameworks",
            source_type=EmbeddingSource.CODE,
            vector_id="vec2",
            file_path="/src/test.py",
            tags=["python", "framework"],
            repository="test-repo",
        )

    def test_initialization(self):
        """Test VectorIndex initialization."""
        index = VectorIndex(embedding_dim=256)
        assert index.embedding_dim == 256
        assert len(index.documents) == 0
        assert len(index.embeddings) == 0
        assert index.created_at is not None

    def test_default_embedding_dim(self):
        """Test default embedding dimension."""
        index = VectorIndex()
        assert index.embedding_dim == 384

    def test_add_document(self):
        """Test adding a single document."""
        doc_id = self.index.add_document(self.sample_doc1)
        
        assert doc_id == "doc1"
        assert len(self.index.documents) == 1
        assert len(self.index.embeddings) == 1
        assert self.sample_doc1.document_id in self.index.documents

    def test_add_document_with_precomputed_embedding(self):
        """Test adding document with pre-computed embedding."""
        embedding = [0.1] * 128
        doc_id = self.index.add_document(self.sample_doc1, embedding)
        
        assert doc_id == "doc1"
        assert len(self.index.documents) == 1
        assert self.index.embeddings[doc_id].vector == embedding

    def test_add_multiple_documents(self):
        """Test adding multiple documents."""
        self.index.add_document(self.sample_doc1)
        self.index.add_document(self.sample_doc2)
        
        assert len(self.index.documents) == 2
        assert len(self.index.embeddings) == 2

    def test_add_documents_batch(self):
        """Test batch document addition."""
        docs = [self.sample_doc1, self.sample_doc2]
        doc_ids = self.index.add_documents_batch(docs)
        
        assert len(doc_ids) == 2
        assert doc_ids == ["doc1", "doc2"]
        assert len(self.index.documents) == 2

    def test_add_documents_batch_empty(self):
        """Test batch addition with empty list."""
        doc_ids = self.index.add_documents_batch([])
        
        assert doc_ids == []
        assert len(self.index.documents) == 0

    def test_search_basic(self):
        """Test basic search functionality."""
        self.index.add_document(self.sample_doc1)
        self.index.add_document(self.sample_doc2)
        
        result = self.index.search("Python programming", top_k=2)
        
        assert result.query_text == "Python programming"
        assert isinstance(result.results, list)
        assert len(result.results) <= 2
        assert hasattr(result, 'query_embedding')

    def test_search_with_threshold(self):
        """Test search respects threshold."""
        self.index.add_document(self.sample_doc1)
        self.index.add_document(self.sample_doc2)
        
        result_high = self.index.search("xyz", top_k=10, threshold=0.9)
        result_low = self.index.search("xyz", top_k=10, threshold=0.0)
        
        # High threshold might return fewer results
        assert len(result_high.results) <= len(result_low.results)

    def test_search_result_structure(self):
        """Test search result has correct structure."""
        self.index.add_document(self.sample_doc1)
        self.index.add_document(self.sample_doc2)
        
        result = self.index.search("Python")
        
        if result.results:
            first_result = result.results[0]
            assert "document_id" in first_result
            assert "title" in first_result
            assert "similarity_score" in first_result
            assert "content_preview" in first_result
            assert "source_type" in first_result
            assert "file_path" in first_result

    def test_search_score_range(self):
        """Test search scores are in valid range."""
        self.index.add_document(self.sample_doc1)
        result = self.index.search("Python testing")
        
        for res in result.results:
            assert 0.0 <= res["similarity_score"] <= 1.0

    def test_search_results_sorted_by_score(self):
        """Test results are sorted by similarity score."""
        self.index.add_document(self.sample_doc1)
        self.index.add_document(self.sample_doc2)
        
        result = self.index.search("Python")
        
        if len(result.results) > 1:
            scores = [r["similarity_score"] for r in result.results]
            assert scores == sorted(scores, reverse=True)

    def test_search_by_embedding(self):
        """Test search using pre-computed embedding."""
        self.index.add_document(self.sample_doc1)
        self.index.add_document(self.sample_doc2)
        
        query_embedding = [0.1] * 128
        results = self.index.search_by_embedding(query_embedding, top_k=2)
        
        assert isinstance(results, list)
        assert all(isinstance(item, tuple) and len(item) == 2 for item in results)

    def test_get_document(self):
        """Test retrieving a document."""
        self.index.add_document(self.sample_doc1)
        
        doc = self.index.get_document("doc1")
        
        assert doc is not None
        assert doc.document_id == "doc1"
        assert doc.title == "Test Document 1"

    def test_get_nonexistent_document(self):
        """Test retrieving non-existent document returns None."""
        doc = self.index.get_document("nonexistent")
        
        assert doc is None

    def test_delete_document(self):
        """Test deleting a document."""
        self.index.add_document(self.sample_doc1)
        assert len(self.index.documents) == 1
        
        deleted = self.index.delete_document("doc1")
        
        assert deleted is True
        assert len(self.index.documents) == 0
        assert len(self.index.embeddings) == 0

    def test_delete_nonexistent_document(self):
        """Test deleting non-existent document."""
        deleted = self.index.delete_document("nonexistent")
        
        assert deleted is False

    def test_update_document(self):
        """Test updating a document."""
        self.index.add_document(self.sample_doc1)
        
        updated_doc = self.index.update_document("doc1", "Updated content")
        
        assert updated_doc is not None
        assert updated_doc.content == "Updated content"
        assert updated_doc.indexed_at is not None

    def test_update_nonexistent_document(self):
        """Test updating non-existent document returns None."""
        updated_doc = self.index.update_document("nonexistent", "content")
        
        assert updated_doc is None

    def test_get_stats_empty_index(self):
        """Test statistics of empty index."""
        stats = self.index.get_stats()
        
        assert stats.total_documents == 0
        assert stats.total_embeddings == 0
        assert stats.vector_dimensions == 128
        assert stats.index_size_mb == 0

    def test_get_stats_populated_index(self):
        """Test statistics of populated index."""
        self.index.add_document(self.sample_doc1)
        self.index.add_document(self.sample_doc2)
        
        stats = self.index.get_stats()
        
        assert stats.total_documents == 2
        assert stats.total_embeddings == 2
        assert stats.vector_dimensions == 128
        assert stats.index_size_mb > 0
        # Sources distribution uses lowercase values
        assert "documentation" in stats.sources_distribution
        assert "code" in stats.sources_distribution

    def test_get_stats_coverage(self):
        """Test coverage calculation in stats."""
        self.index.add_document(self.sample_doc1)
        self.index.add_document(self.sample_doc2)
        
        stats = self.index.get_stats()
        
        assert "test-repo" in stats.coverage
        assert stats.coverage["test-repo"] == 100.0

    def test_export_to_json(self):
        """Test exporting index to JSON."""
        self.index.add_document(self.sample_doc1)
        self.index.add_document(self.sample_doc2)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filepath = f.name
        
        try:
            success = self.index.export_to_json(filepath)
            
            assert success is True
            
            # Verify file contents
            data = json.loads(Path(filepath).read_text())
            assert data["documents"] == 2
            assert data["embedding_dim"] == 128
            assert len(data["documents_list"]) == 2
        finally:
            Path(filepath).unlink(missing_ok=True)

    def test_export_to_json_invalid_path(self):
        """Test export to invalid path."""
        filepath = "/invalid/path/that/does/not/exist/file.json"
        success = self.index.export_to_json(filepath)
        
        assert success is False

    def test_import_from_json(self):
        """Test importing index from JSON."""
        # First export
        self.index.add_document(self.sample_doc1)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filepath = f.name
        
        try:
            self.index.export_to_json(filepath)
            
            # Then import to new index
            new_index = VectorIndex()
            success = new_index.import_from_json(filepath)
            
            assert success is True
        finally:
            Path(filepath).unlink(missing_ok=True)

    def test_import_from_nonexistent_file(self):
        """Test importing from non-existent file."""
        filepath = "/tmp/nonexistent_index_file_xyz.json"
        success = self.index.import_from_json(filepath)
        
        assert success is False

    def test_clear_index(self):
        """Test clearing the index."""
        self.index.add_document(self.sample_doc1)
        self.index.add_document(self.sample_doc2)
        
        assert len(self.index.documents) == 2
        
        self.index.clear()
        
        assert len(self.index.documents) == 0
        assert len(self.index.embeddings) == 0

    def test_len_operator(self):
        """Test __len__ operator."""
        assert len(self.index) == 0
        
        self.index.add_document(self.sample_doc1)
        assert len(self.index) == 1
        
        self.index.add_document(self.sample_doc2)
        assert len(self.index) == 2
        
        self.index.delete_document("doc1")
        assert len(self.index) == 1

    def test_multiple_documents_same_repository(self):
        """Test handling multiple documents from same repository."""
        doc1 = IndexedDocument(
            document_id="repo_doc1",
            title="Repo Doc 1",
            content="Content 1",
            source_type=EmbeddingSource.CODE,
            vector_id="vec1",
            repository="shared-repo",
        )
        doc2 = IndexedDocument(
            document_id="repo_doc2",
            title="Repo Doc 2",
            content="Content 2",
            source_type=EmbeddingSource.DOCUMENTATION,
            vector_id="vec2",
            repository="shared-repo",
        )
        
        self.index.add_document(doc1)
        self.index.add_document(doc2)
        
        stats = self.index.get_stats()
        assert stats.coverage["shared-repo"] == 100.0

    def test_documents_from_different_repositories(self):
        """Test handling documents from different repositories."""
        doc1 = IndexedDocument(
            document_id="repo1_doc",
            title="Repo 1 Doc",
            content="Content 1",
            source_type=EmbeddingSource.CODE,
            vector_id="vec1",
            repository="repo1",
        )
        doc2 = IndexedDocument(
            document_id="repo2_doc",
            title="Repo 2 Doc",
            content="Content 2",
            source_type=EmbeddingSource.CODE,
            vector_id="vec2",
            repository="repo2",
        )
        
        self.index.add_document(doc1)
        self.index.add_document(doc2)
        
        stats = self.index.get_stats()
        assert len(stats.coverage) == 2
        assert stats.coverage["repo1"] == 50.0
        assert stats.coverage["repo2"] == 50.0

    def test_search_time_tracking(self):
        """Test that search time is tracked."""
        self.index.add_document(self.sample_doc1)
        
        result = self.index.search("Python")
        
        assert result.search_time_ms > 0
        assert isinstance(result.search_time_ms, float)

    def test_query_embedding_in_search_result(self):
        """Test query embedding is returned in search result."""
        self.index.add_document(self.sample_doc1)
        
        result = self.index.search("Python")
        
        assert result.query_embedding is not None
        assert isinstance(result.query_embedding, list)
        assert len(result.query_embedding) == 128

    def test_document_with_tags(self):
        """Test documents with tags."""
        self.index.add_document(self.sample_doc1)
        
        doc = self.index.get_document("doc1")
        assert doc.tags == ["python", "testing"]

    def test_search_preview_length(self):
        """Test content preview length in search results."""
        self.index.add_document(self.sample_doc1)
        
        result = self.index.search("Python")
        
        if result.results:
            preview = result.results[0]["content_preview"]
            assert len(preview) <= 200

    def test_update_preserves_document_id(self):
        """Test that update preserves document ID."""
        self.index.add_document(self.sample_doc1)
        
        updated = self.index.update_document("doc1", "New content")
        
        assert updated.document_id == "doc1"

    def test_batch_add_preserves_order(self):
        """Test batch add preserves document order."""
        docs = [self.sample_doc1, self.sample_doc2]
        doc_ids = self.index.add_documents_batch(docs)
        
        for expected_id, returned_id in zip(["doc1", "doc2"], doc_ids):
            assert expected_id == returned_id
            assert self.index.get_document(returned_id) is not None

    def test_search_empty_index(self):
        """Test search on empty index."""
        result = self.index.search("query")
        
        assert result.results == []
        assert result.search_time_ms >= 0

    def test_search_top_k_parameter(self):
        """Test top_k parameter limits results."""
        self.index.add_document(self.sample_doc1)
        self.index.add_document(self.sample_doc2)
        
        result = self.index.search("Python", top_k=1)
        
        assert len(result.results) <= 1

    def test_export_json_structure(self):
        """Test exported JSON has correct structure."""
        self.index.add_document(self.sample_doc1)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filepath = f.name
        
        try:
            self.index.export_to_json(filepath)
            
            data = json.loads(Path(filepath).read_text())
            
            assert "created_at" in data
            assert "embedding_dim" in data
            assert "documents" in data
            assert "documents_list" in data
            assert isinstance(data["documents_list"], list)
        finally:
            Path(filepath).unlink(missing_ok=True)
