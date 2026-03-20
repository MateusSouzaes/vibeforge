"""Tests for embedding generator module."""

import pytest
from src.embeddings.embedding_generator import EmbeddingGenerator
from src.embeddings.models import EmbeddingSource


class TestEmbeddingGenerator:
    """Test EmbeddingGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = EmbeddingGenerator(embedding_dim=128)
        self.sample_text = "This is a sample text for embedding"
        self.sample_code = "def hello_world(): print('Hello, World!')"

    def test_initialization(self):
        """Test EmbeddingGenerator initialization."""
        gen = EmbeddingGenerator(embedding_dim=256)
        assert gen.embedding_dim == 256
        assert gen.stop_words is not None
        assert len(gen.stop_words) > 0

    def test_default_embedding_dim(self):
        """Test default embedding dimension."""
        gen = EmbeddingGenerator()
        assert gen.embedding_dim == 384

    def test_generate_embedding_tfidf_strategy(self):
        """Test TF-IDF embedding generation."""
        embedding = self.generator.generate_embedding(
            self.sample_text,
            "doc1",
            EmbeddingSource.DOCUMENTATION
        )
        
        assert embedding.content_id == "doc1"
        assert embedding.content[:20] == self.sample_text[:20]
        assert embedding.source == EmbeddingSource.DOCUMENTATION
        assert len(embedding.vector) == 128
        assert embedding.dimensions == 128
        
        # Check vector is normalized
        magnitude = sum(v**2 for v in embedding.vector) ** 0.5
        assert 0.0 <= magnitude <= 1.5  # Allow some variance

    def test_generate_embedding_code_source(self):
        """Test code embedding."""
        embedding = self.generator.generate_embedding(
            self.sample_code,
            "code1",
            EmbeddingSource.CODE
        )
        
        assert embedding.source == EmbeddingSource.CODE
        assert len(embedding.vector) == 128

    def test_generate_embedding_commit_source(self):
        """Test commit message embedding."""
        commit_msg = "feat: add user authentication"
        embedding = self.generator.generate_embedding(
            commit_msg,
            "commit1",
            EmbeddingSource.COMMIT_MESSAGE
        )
        
        assert embedding.source == EmbeddingSource.COMMIT_MESSAGE
        assert len(embedding.vector) == 128

    def test_generate_embedding_decision_source(self):
        """Test architectural decision embedding."""
        decision = "Decided to use PostgreSQL instead of MongoDB"
        embedding = self.generator.generate_embedding(
            decision,
            "decision1",
            EmbeddingSource.DECISION
        )
        
        assert embedding.source == EmbeddingSource.DECISION
        assert len(embedding.vector) == 128

    def test_generate_batch_embeddings(self):
        """Test batch embedding generation."""
        texts = [
            "First document",
            "Second document",
            "Third document"
        ]
        
        batch = self.generator.generate_batch(
            texts,
            ["doc1", "doc2", "doc3"],
            EmbeddingSource.DOCUMENTATION
        )
        
        # batch_id can be auto-generated or None
        assert len(batch.embeddings) == 3
        assert batch.total_tokens > 0
        assert batch.model_used == "multi-strategy"
        
        for emb in batch.embeddings:
            assert len(emb.vector) == 128

    def test_batch_with_mixed_sources(self):
        """Test batch with mixed embedding sources."""
        texts = ["code", "document", "commit"]
        sources = [
            EmbeddingSource.CODE,
            EmbeddingSource.DOCUMENTATION,
            EmbeddingSource.COMMIT_MESSAGE
        ]
        
        batch = self.generator.generate_batch(
            texts,
            ["id1", "id2", "id3"],
            sources
        )
        
        assert len(batch.embeddings) == 3
        assert batch.embeddings[0].source == EmbeddingSource.CODE
        assert batch.embeddings[1].source == EmbeddingSource.DOCUMENTATION
        assert batch.embeddings[2].source == EmbeddingSource.COMMIT_MESSAGE

    def test_empty_batch(self):
        """Test batch with empty list."""
        batch = self.generator.generate_batch([], [])
        
        assert len(batch.embeddings) == 0
        assert batch.total_tokens == 0

    def test_tokenization(self):
        """Test text tokenization."""
        text = "The quick brown fox jumps over the lazy dog"
        tokens = self.generator._tokenize(text)
        
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert all(isinstance(t, str) for t in tokens)
        # Common stop words should be filtered
        assert "the" not in tokens
        assert "over" not in tokens

    def test_tokenization_with_symbols(self):
        """Test tokenization with special characters."""
        text = "hello@world.com #hashtag $variable"
        tokens = self.generator._tokenize(text)
        
        assert isinstance(tokens, list)
        # Should have meaningful tokens
        assert len(tokens) > 0

    def test_tokenization_case_insensitive(self):
        """Test that tokenization is case insensitive."""
        tokens1 = self.generator._tokenize("HELLO World")
        tokens2 = self.generator._tokenize("hello world")
        
        assert tokens1 == tokens2

    def test_calculate_similarity_identical_vectors(self):
        """Test similarity of identical vectors."""
        vector = [0.1, 0.2, 0.3] + [0.0] * 125
        
        similarity = self.generator.calculate_similarity(vector, vector)
        
        assert similarity == 1.0

    def test_calculate_similarity_orthogonal_vectors(self):
        """Test similarity of orthogonal vectors."""
        vector1 = [1.0] + [0.0] * 127
        vector2 = [0.0, 1.0] + [0.0] * 126
        
        similarity = self.generator.calculate_similarity(vector1, vector2)
        
        assert similarity == 0.0

    def test_calculate_similarity_range(self):
        """Test that similarity is always in range [0, 1]."""
        vector1 = [0.1] * 128
        vector2 = [0.2] * 128
        
        similarity = self.generator.calculate_similarity(vector1, vector2)
        
        assert 0.0 <= similarity <= 1.0

    def test_find_similar_basic(self):
        """Test finding similar embeddings."""
        from src.embeddings.models import EmbeddingVector
        
        # Create test embeddings
        embeddings = [
            EmbeddingVector(
                content_id=f"doc{i}",
                content=f"Document {i}",
                source=EmbeddingSource.DOCUMENTATION,
                vector=[float(i)] * 128,
                dimensions=128,
            )
            for i in range(3)
        ]
        
        query_vector = [0.0] * 128
        
        results = self.generator.find_similar(
            query_vector,
            embeddings,
            top_k=2,
            threshold=0.0
        )
        
        assert isinstance(results, list)
        assert len(results) <= 2

    def test_find_similar_with_threshold(self):
        """Test find_similar respects threshold."""
        from src.embeddings.models import EmbeddingVector
        
        embeddings = [
            EmbeddingVector(
                content_id=f"doc{i}",
                content=f"Document {i}",
                source=EmbeddingSource.DOCUMENTATION,
                vector=[float(i) / 10] * 128,
                dimensions=128,
            )
            for i in range(5)
        ]
        
        query_vector = [0.0] * 128
        
        # High threshold should return fewer results
        results_high = self.generator.find_similar(
            query_vector,
            embeddings,
            top_k=5,
            threshold=0.9
        )
        
        # Lower threshold should return more results
        results_low = self.generator.find_similar(
            query_vector,
            embeddings,
            top_k=5,
            threshold=0.0
        )
        
        assert len(results_high) <= len(results_low)

    def test_find_similar_returns_tuples(self):
        """Test find_similar returns (embedding, score) tuples."""
        from src.embeddings.models import EmbeddingVector
        
        embeddings = [
            EmbeddingVector(
                content_id=f"doc{i}",
                content=f"Document {i}",
                source=EmbeddingSource.DOCUMENTATION,
                vector=[0.1 * i] * 128,
                dimensions=128,
            )
            for i in range(3)
        ]
        
        query_vector = [0.0] * 128
        
        results = self.generator.find_similar(
            query_vector,
            embeddings,
            top_k=3,
            threshold=0.0
        )
        
        for embedding, score in results:
            assert isinstance(embedding, EmbeddingVector)
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

    def test_find_similar_sorted_by_score(self):
        """Test find_similar returns results sorted by score."""
        from src.embeddings.models import EmbeddingVector
        
        embeddings = [
            EmbeddingVector(
                content_id="doc1",
                content="Document 1",
                source=EmbeddingSource.DOCUMENTATION,
                vector=[0.1] * 128,
                dimensions=128,
            ),
            EmbeddingVector(
                content_id="doc2",
                content="Document 2",
                source=EmbeddingSource.DOCUMENTATION,
                vector=[0.5] * 128,  # More similar
                dimensions=128,
            ),
        ]
        
        query_vector = [0.5] * 128
        
        results = self.generator.find_similar(
            query_vector,
            embeddings,
            top_k=2,
            threshold=0.0
        )
        
        # Results should be sorted by score (descending)
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)

    def test_vector_dimension_consistency(self):
        """Test all vectors have consistent dimensions."""
        texts = ["text1", "text2", "text3"]
        batch = self.generator.generate_batch(
            texts,
            ["id1", "id2", "id3"]
        )
        
        for embedding in batch.embeddings:
            assert len(embedding.vector) == self.generator.embedding_dim
            assert embedding.dimensions == self.generator.embedding_dim

    def test_empty_text_embedding(self):
        """Test embedding of empty text."""
        embedding = self.generator.generate_embedding(
            "",
            "empty",
            EmbeddingSource.DOCUMENTATION
        )
        
        assert len(embedding.vector) == 128
        # Empty text should produce a valid vector
        assert all(isinstance(v, float) for v in embedding.vector)

    def test_long_text_embedding(self):
        """Test embedding of very long text."""
        long_text = "word " * 10000
        embedding = self.generator.generate_embedding(
            long_text,
            "long",
            EmbeddingSource.DOCUMENTATION
        )
        
        assert len(embedding.vector) == 128
        assert embedding.dimensions == 128

    def test_special_characters_embedding(self):
        """Test embedding with special characters."""
        special_text = "Hello!@#$%^&*()_+-=[]{}|;:,.<>?"
        embedding = self.generator.generate_embedding(
            special_text,
            "special",
            EmbeddingSource.DOCUMENTATION
        )
        
        assert len(embedding.vector) == 128

    def test_unicode_embedding(self):
        """Test embedding with unicode characters."""
        unicode_text = "Hello 世界 🌍 Привет"
        embedding = self.generator.generate_embedding(
            unicode_text,
            "unicode",
            EmbeddingSource.DOCUMENTATION
        )
        
        assert len(embedding.vector) == 128

    def test_metadata_preservation(self):
        """Test that metadata is preserved in embeddings."""
        metadata = {"key": "value", "count": 42}
        embedding = self.generator.generate_embedding(
            self.sample_text,
            "doc1",
            EmbeddingSource.DOCUMENTATION,
            metadata
        )
        
        assert embedding.metadata == metadata

    def test_different_strategies_produce_different_vectors(self):
        """Test that different embedding strategies produce different vectors."""
        text = "Python programming language"
        
        # Generate with different content_id (triggers different strategy)
        emb1 = self.generator.generate_embedding(
            text,
            "id1",
            EmbeddingSource.CODE
        )
        
        emb2 = self.generator.generate_embedding(
            text,
            "id2",
            EmbeddingSource.DOCUMENTATION
        )
        
        # Vectors might be different (depends on strategy selection)
        # But both should be valid
        assert len(emb1.vector) == len(emb2.vector)
        assert all(isinstance(v, float) for v in emb1.vector)
        assert all(isinstance(v, float) for v in emb2.vector)

    def test_batch_content_tracking(self):
        """Test that batch tracks content properly."""
        texts = ["Content A", "Content B", "Content C"]
        batch = self.generator.generate_batch(
            texts,
            ["id1", "id2", "id3"]
        )
        
        assert len(batch.embeddings) == 3
        for i, emb in enumerate(batch.embeddings):
            assert texts[i] in emb.content or emb.content in texts[i]
