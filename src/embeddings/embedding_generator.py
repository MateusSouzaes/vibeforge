"""Generate embeddings for code and text content."""

import hashlib
import math
from typing import List, Dict, Optional, Tuple
from collections import Counter
from src.embeddings.models import EmbeddingVector, EmbeddingSource, EmbeddingBatch


class EmbeddingGenerator:
    """Generate embeddings for code and text using multiple strategies."""

    def __init__(self, embedding_dim: int = 384, strategy: str = "tfidf"):
        """Initialize embedding generator.
        
        Args:
            embedding_dim: Dimension of embedding vectors
            strategy: Strategy to use ("tfidf", "hash", "semantic")
        """
        self.embedding_dim = embedding_dim
        self.strategy = strategy
        self.vocabulary = {}
        self.document_frequencies = {}
        self.total_documents = 0
        self.stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "is", "are", "was", "were", "be", "been", "being", "over",
            "by", "from", "as", "it", "that", "this", "you", "he", "she", "we", "they",
            "do", "does", "did", "have", "has", "had", "will", "would", "should", "can",
            "could", "may", "might", "must", "if", "while"
        }

    def generate_embedding(
        self,
        content: str,
        content_id: str,
        source: EmbeddingSource = EmbeddingSource.CODE,
        metadata: Optional[Dict] = None
    ) -> EmbeddingVector:
        """Generate embedding for a piece of content.
        
        Args:
            content: Text/code to embed
            content_id: Unique identifier
            source: Source type of content
            metadata: Additional metadata
            
        Returns:
            EmbeddingVector with generated embedding
        """
        metadata = metadata or {}
        
        if self.strategy == "tfidf":
            vector = self._generate_tfidf_embedding(content)
        elif self.strategy == "hash":
            vector = self._generate_hash_embedding(content)
        elif self.strategy == "semantic":
            vector = self._generate_semantic_embedding(content)
        else:
            vector = self._generate_hash_embedding(content)
        
        return EmbeddingVector(
            content_id=content_id,
            content=content[:500],  # Store truncated content
            source=source,
            vector=vector,
            dimensions=len(vector),
            metadata=metadata,
        )

    def generate_batch(
        self,
        texts: List[str],
        content_ids: List[str],
        sources: Optional[List[EmbeddingSource]] = None,
    ) -> EmbeddingBatch:
        """Generate embeddings for a batch of content.
        
        Args:
            texts: List of text/code to embed
            content_ids: List of unique identifiers
            sources: List of source types (defaults to CODE)
            
        Returns:
            EmbeddingBatch with all embeddings
        """
        embeddings = []
        total_tokens = 0
        
        # Handle default sources
        if sources is None:
            sources = [EmbeddingSource.CODE] * len(texts)
        elif isinstance(sources, EmbeddingSource):
            # Single source for all
            sources = [sources] * len(texts)
        
        # Handle mixed sources (list with one or multiple items)
        if len(sources) == 1 and len(texts) > 1:
            sources = sources * len(texts)
        
        for text, content_id, source in zip(texts, content_ids, sources):
            embedding = self.generate_embedding(text, content_id, source)
            embeddings.append(embedding)
            total_tokens += len(text.split())
        
        return EmbeddingBatch(
            batch_id=None,  # Auto-generate if needed
            embeddings=embeddings,
            total_tokens=total_tokens,
            model_used="multi-strategy",
        )

    def _generate_tfidf_embedding(self, content: str) -> List[float]:
        """Generate TF-IDF based embedding.
        
        Args:
            content: Text to embed
            
        Returns:
            Embedding vector
        """
        # Tokenize
        tokens = self._tokenize(content)
        
        # Calculate TF (term frequency)
        tf = Counter(tokens)
        total_terms = len(tokens)
        
        # Create embedding vector based on top features
        vector = []
        
        # Sort tokens by frequency
        top_tokens = tf.most_common(self.embedding_dim)
        
        for _ in range(self.embedding_dim):
            if top_tokens:
                token, count = top_tokens.pop(0)
                tf_score = count / max(total_terms, 1)
                vector.append(tf_score)
            else:
                vector.append(0.0)
        
        # Normalize
        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        
        return vector

    def _generate_hash_embedding(self, content: str) -> List[float]:
        """Generate hash-based embedding.
        
        Args:
            content: Text to embed
            
        Returns:
            Embedding vector from content hash
        """
        # Create hash of content
        hash_obj = hashlib.sha256(content.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert hash bytes to float vector
        vector = []
        for i in range(self.embedding_dim):
            byte_idx = i % len(hash_bytes)
            byte_val = hash_bytes[byte_idx]
            # Normalize byte to [0, 1]
            float_val = byte_val / 255.0
            vector.append(float_val)
        
        # Add some content-based variation
        tokens = self._tokenize(content)
        if tokens:
            freq = Counter(tokens)
            for i, (token, count) in enumerate(freq.most_common(self.embedding_dim)):
                if i < len(vector):
                    vector[i] = (vector[i] + count / len(tokens)) / 2.0
        
        # Normalize
        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        
        return vector

    def _generate_semantic_embedding(self, content: str) -> List[float]:
        """Generate semantic embedding using keyword analysis.
        
        Args:
            content: Text to embed
            
        Returns:
            Embedding vector based on semantic features
        """
        tokens = self._tokenize(content)
        vector = [0.0] * self.embedding_dim
        
        # Identify semantic categories
        code_keywords = {"def", "class", "function", "import", "return", "if", "for", "while"}
        doc_keywords = {"documentation", "example", "parameter", "return", "description"}
        
        keyword_scores = {
            "code": sum(1 for t in tokens if t in code_keywords),
            "documentation": sum(1 for t in tokens if t in doc_keywords),
            "complexity": len(set(tokens)),  # Vocabulary diversity
            "density": len(tokens) / max(len(content), 1),
        }
        
        # Create semantic vector
        for i, (category, score) in enumerate(keyword_scores.items()):
            if i < len(vector):
                vector[i] = min(1.0, score / max(len(tokens), 1))
        
        # Fill remaining dimensions with token frequency info
        freq_scores = Counter(tokens).most_common(self.embedding_dim - len(keyword_scores))
        for i, (token, freq) in enumerate(freq_scores):
            idx = len(keyword_scores) + i
            if idx < len(vector):
                vector[idx] = min(1.0, freq / len(tokens))
        
        # Normalize
        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        
        return vector

    def _tokenize(self, content: str) -> List[str]:
        """Tokenize content into words.
        
        Args:
            content: Text to tokenize
            
        Returns:
            List of tokens
        """
        # Simple tokenization
        import re
        # Convert to lowercase and split on non-alphanumeric
        tokens = re.findall(r'\b[a-z0-9_]+\b', content.lower())
        
        # Filter short tokens and common words (using self.stop_words)
        tokens = [t for t in tokens if len(t) > 2 and t not in self.stop_words]
        
        return tokens

    def calculate_similarity(
        self,
        vector1: List[float],
        vector2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors.
        
        Args:
            vector1: First embedding vector
            vector2: Second embedding vector
            
        Returns:
            Similarity score (0.0-1.0)
        """
        if len(vector1) != len(vector2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vector1, vector2))
        magnitude1 = math.sqrt(sum(a * a for a in vector1))
        magnitude2 = math.sqrt(sum(b * b for b in vector2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        cosine_similarity = dot_product / (magnitude1 * magnitude2)
        
        # Clamp to [0, 1] range (normalized embeddings typically produce positive similarity)
        return max(0.0, min(1.0, cosine_similarity))

    def find_similar(
        self,
        query_vector: List[float],
        embeddings: List[EmbeddingVector],
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Tuple[EmbeddingVector, float]]:
        """Find similar embeddings to query vector.
        
        Args:
            query_vector: Query embedding
            embeddings: List of embeddings to search
            top_k: Number of top results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of (embedding, similarity_score) tuples
        """
        similarities = []
        
        for embedding in embeddings:
            similarity = self.calculate_similarity(query_vector, embedding.vector)
            
            if similarity >= threshold:
                similarities.append((embedding, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
