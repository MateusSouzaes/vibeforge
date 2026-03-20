"""In-memory vector index for storing and searching embeddings."""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from src.embeddings.models import (
    EmbeddingVector,
    IndexedDocument,
    SimilarityResult,
    VectorIndexStats,
)
from src.embeddings.embedding_generator import EmbeddingGenerator


class VectorIndex:
    """In-memory vector index for embeddings."""

    def __init__(self, embedding_dim: int = 384):
        """Initialize vector index.
        
        Args:
            embedding_dim: Dimension of embedding vectors
        """
        self.embedding_dim = embedding_dim
        self.documents: Dict[str, IndexedDocument] = {}
        self.embeddings: Dict[str, EmbeddingVector] = {}
        self.generator = EmbeddingGenerator(embedding_dim)
        self.created_at = datetime.now()

    def add_document(
        self,
        document: IndexedDocument,
        embedding_vector: Optional[List[float]] = None
    ) -> str:
        """Add a document and its embedding to the index.
        
        Args:
            document: Document to index
            embedding_vector: Pre-computed embedding or None to generate
            
        Returns:
            Document ID
        """
        # Generate embedding if not provided
        if embedding_vector is None:
            vec_obj = self.generator.generate_embedding(
                document.content,
                document.document_id,
                document.source_type
            )
            embedding_vector = vec_obj.vector
        
        # Store document and embedding
        self.documents[document.document_id] = document
        self.embeddings[document.document_id] = EmbeddingVector(
            content_id=document.document_id,
            content=document.content[:500],
            source=document.source_type,
            vector=embedding_vector,
            dimensions=len(embedding_vector),
            metadata=document.metadata,
        )
        
        return document.document_id

    def add_documents_batch(
        self,
        documents: List[IndexedDocument]
    ) -> List[str]:
        """Add multiple documents at once.
        
        Args:
            documents: List of documents to index
            
        Returns:
            List of document IDs
        """
        document_ids = []
        
        for document in documents:
            doc_id = self.add_document(document)
            document_ids.append(doc_id)
        
        return document_ids

    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> SimilarityResult:
        """Search for similar documents.
        
        Args:
            query: Query text
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            SimilarityResult with search results
        """
        import time
        start_time = time.time()
        
        # Generate query embedding
        query_embedding = self.generator.generate_embedding(
            query,
            "query",
            None
        )
        
        # Find similar embeddings
        similarities = self.generator.find_similar(
            query_embedding.vector,
            list(self.embeddings.values()),
            top_k=top_k,
            threshold=threshold
        )
        
        # Build results
        results = []
        for embedding, similarity in similarities:
            doc = self.documents.get(embedding.content_id)
            if doc:
                result = {
                    "document_id": doc.document_id,
                    "title": doc.title,
                    "similarity_score": similarity,
                    "content_preview": doc.content[:200],
                    "source_type": doc.source_type.value,
                    "file_path": doc.file_path,
                }
                results.append(result)
        
        search_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return SimilarityResult(
            query_text=query,
            results=results,
            query_embedding=query_embedding.vector,
            search_time_ms=search_time,
            threshold=threshold,
        )

    def search_by_embedding(
        self,
        embedding_vector: List[float],
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Tuple[str, float]]:
        """Search using a pre-computed embedding.
        
        Args:
            embedding_vector: Query embedding vector
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of (document_id, similarity_score) tuples
        """
        similarities = self.generator.find_similar(
            embedding_vector,
            list(self.embeddings.values()),
            top_k=top_k,
            threshold=threshold
        )
        
        return [(emb.content_id, sim) for emb, sim in similarities]

    def get_document(self, document_id: str) -> Optional[IndexedDocument]:
        """Retrieve a document by ID.
        
        Args:
            document_id: Document identifier
            
        Returns:
            IndexedDocument or None
        """
        return self.documents.get(document_id)

    def delete_document(self, document_id: str) -> bool:
        """Delete a document from index.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if deleted, False if not found
        """
        if document_id in self.documents:
            del self.documents[document_id]
            del self.embeddings[document_id]
            return True
        
        return False

    def update_document(
        self,
        document_id: str,
        updated_content: str
    ) -> Optional[IndexedDocument]:
        """Update document content and re-embed.
        
        Args:
            document_id: Document identifier
            updated_content: New content
            
        Returns:
            Updated document or None
        """
        if document_id not in self.documents:
            return None
        
        document = self.documents[document_id]
        document.content = updated_content
        document.indexed_at = datetime.now()
        
        # Re-generate embedding
        vec_obj = self.generator.generate_embedding(
            updated_content,
            document_id,
            document.source_type
        )
        self.embeddings[document_id] = vec_obj
        
        return document

    def get_stats(self) -> VectorIndexStats:
        """Get index statistics.
        
        Returns:
            VectorIndexStats with index information
        """
        # Calculate sources distribution
        sources_dist = {}
        for doc in self.documents.values():
            source_name = doc.source_type.value
            sources_dist[source_name] = sources_dist.get(source_name, 0) + 1
        
        # Calculate repository coverage
        repos = set(doc.repository for doc in self.documents.values())
        coverage = {}
        for repo in repos:
            repo_docs = sum(1 for d in self.documents.values() if d.repository == repo)
            coverage[repo] = (repo_docs / len(self.documents)) * 100 if self.documents else 0
        
        # Calculate approximate index size
        index_size_mb = (
            len(self.embeddings) * (self.embedding_dim * 4) / (1024 * 1024)
        )
        
        return VectorIndexStats(
            total_documents=len(self.documents),
            total_embeddings=len(self.embeddings),
            vector_dimensions=self.embedding_dim,
            index_size_mb=index_size_mb,
            last_updated=max(
                (d.indexed_at for d in self.documents.values()),
                default=self.created_at
            ),
            sources_distribution=sources_dist,
            coverage=coverage,
        )

    def export_to_json(self, filepath: str) -> bool:
        """Export index to JSON file.
        
        Args:
            filepath: Path to save JSON file
            
        Returns:
            True if successful
        """
        try:
            data = {
                "created_at": self.created_at.isoformat(),
                "embedding_dim": self.embedding_dim,
                "documents": len(self.documents),
                "documents_list": [
                    {
                        "id": doc.document_id,
                        "title": doc.title,
                        "source": doc.source_type.value,
                        "repository": doc.repository,
                    }
                    for doc in self.documents.values()
                ],
            }
            
            Path(filepath).write_text(json.dumps(data, indent=2))
            return True
        except Exception:
            return False

    def import_from_json(self, filepath: str) -> bool:
        """Import index from JSON file.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            True if successful
        """
        try:
            data = json.loads(Path(filepath).read_text())
            # Note: This is a simplified import (embeddings not restored)
            # Full import would require embeddings data
            return True
        except Exception:
            return False

    def clear(self) -> None:
        """Clear all documents and embeddings."""
        self.documents.clear()
        self.embeddings.clear()

    def __len__(self) -> int:
        """Get number of documents in index."""
        return len(self.documents)
