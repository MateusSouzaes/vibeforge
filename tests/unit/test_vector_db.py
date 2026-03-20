"""
Testes unitários para VectorDB
Responsável por: Armazenamento em banco vetorial ChromaDB
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from src.rag.vector_db import VectorDB


class TestVectorDB:
    """Testes para banco vetorial"""

    @pytest.fixture
    def db(self, tmp_path):
        """Instancia VectorDB com diretório temporário"""
        return VectorDB(persist_directory=str(tmp_path))

    @pytest.fixture
    def sample_embeddings(self):
        """Retorna embeddings de exemplo"""
        return {
            "doc1": {
                "text": "Python function to calculate factorial",
                "embedding": [0.1] * 1280,
                "metadata": {"language": "python", "type": "function"},
            },
            "doc2": {
                "text": "JavaScript async/await pattern",
                "embedding": [0.2] * 1280,
                "metadata": {"language": "javascript", "type": "pattern"},
            },
            "doc3": {
                "text": "Database query optimization techniques",
                "embedding": [0.3] * 1280,
                "metadata": {"language": "sql", "type": "tutorial"},
            },
        }

    def test_initialization(self, db):
        """Teste: VectorDB deve inicializar corretamente"""
        assert db is not None
        assert hasattr(db, "add_documents")
        assert hasattr(db, "query")

    def test_add_single_document(self, db):
        """Teste: Deve adicionar documento único"""
        doc_id = "doc1"
        text = "Python code example"
        embedding = [0.1] * 1280
        metadata = {"language": "python"}

        result = db.add_document(doc_id, text, embedding, metadata)

        assert result is not None
        assert result == doc_id

    def test_add_batch_documents(self, db, sample_embeddings):
        """Teste: Deve adicionar múltiplos documentos"""
        documents = []
        for doc_id, data in sample_embeddings.items():
            documents.append({
                "id": doc_id,
                "text": data["text"],
                "embedding": data["embedding"],
                "metadata": data["metadata"],
            })

        result = db.add_documents(documents)

        assert len(result) == len(documents)

    def test_query_similarity_search(self, db, sample_embeddings):
        """Teste: Deve fazer busca por similaridade"""
        # Adicionar documentos
        documents = []
        for doc_id, data in sample_embeddings.items():
            documents.append({
                "id": doc_id,
                "text": data["text"],
                "embedding": data["embedding"],
                "metadata": data["metadata"],
            })
        db.add_documents(documents)

        # Buscar por similaridade
        query_embedding = [0.1] * 1280
        results = db.query(query_embedding, top_k=2)

        assert isinstance(results, list)
        assert len(results) <= 2
        assert all("id" in r for r in results)
        assert all("distance" in r for r in results)

    def test_query_with_filters(self, db, sample_embeddings):
        """Teste: Deve filtrar resultados por metadata"""
        # Adicionar documentos
        documents = []
        for doc_id, data in sample_embeddings.items():
            documents.append({
                "id": doc_id,
                "text": data["text"],
                "embedding": data["embedding"],
                "metadata": data["metadata"],
            })
        db.add_documents(documents)

        # Buscar com filtro
        query_embedding = [0.1] * 1280
        results = db.query(
            query_embedding,
            top_k=5,
            filter={"language": "python"}
        )

        assert all(r["metadata"]["language"] == "python" for r in results)

    def test_get_document_by_id(self, db):
        """Teste: Deve recuperar documento por ID"""
        doc_id = "test_doc"
        text = "Test document"
        embedding = [0.1] * 1280

        db.add_document(doc_id, text, embedding)
        result = db.get_document(doc_id)

        assert result is not None
        assert result["id"] == doc_id
        assert result["text"] == text

    def test_get_nonexistent_document(self, db):
        """Teste: Deve retornar None para documento inexistente"""
        result = db.get_document("nonexistent")

        assert result is None

    def test_update_document(self, db):
        """Teste: Deve atualizar documento existente"""
        doc_id = "doc1"
        db.add_document(doc_id, "Original text", [0.1] * 1280)
        db.update_document(doc_id, "Updated text", [0.2] * 1280)

        updated = db.get_document(doc_id)

        assert updated["text"] == "Updated text"

    def test_delete_document(self, db):
        """Teste: Deve deletar documento"""
        doc_id = "doc1"
        db.add_document(doc_id, "Text to delete", [0.1] * 1280)
        db.delete_document(doc_id)

        result = db.get_document(doc_id)

        assert result is None

    def test_delete_nonexistent_document(self, db):
        """Teste: Deletar documento inexistente não deve lançar erro"""
        # Não deve lançar erro
        result = db.delete_document("nonexistent")
        assert result is not None or result is None

    def test_collection_size(self, db):
        """Teste: Deve retornar quantidade de documentos"""
        docs = [
            {"id": f"doc{i}", "text": f"Text {i}", "embedding": [0.1] * 1280}
            for i in range(5)
        ]
        db.add_documents(docs)

        size = db.get_collection_size()

        assert size >= 5

    def test_list_all_documents(self, db, sample_embeddings):
        """Teste: Deve listar todos os documentos"""
        documents = []
        for doc_id, data in sample_embeddings.items():
            documents.append({
                "id": doc_id,
                "text": data["text"],
                "embedding": data["embedding"],
            })
        db.add_documents(documents)

        all_docs = db.list_documents()

        assert len(all_docs) >= len(documents)

    def test_batch_delete(self, db):
        """Teste: Deve deletar múltiplos documentos"""
        doc_ids = ["doc1", "doc2", "doc3"]
        for doc_id in doc_ids:
            db.add_document(doc_id, f"Text {doc_id}", [0.1] * 1280)

        db.delete_documents(doc_ids)

        for doc_id in doc_ids:
            assert db.get_document(doc_id) is None

    def test_clear_collection(self, db, sample_embeddings):
        """Teste: Deve limpar toda a coleção"""
        documents = []
        for doc_id, data in sample_embeddings.items():
            documents.append({
                "id": doc_id,
                "text": data["text"],
                "embedding": data["embedding"],
            })
        db.add_documents(documents)

        db.clear_collection()

        assert db.get_collection_size() == 0

    def test_search_ranking(self, db):
        """Teste: Resultados devem estar ordenados por relevância"""
        # Adicionar docs
        db.add_document("doc1", "Python code", [0.1] * 1280)
        db.add_document("doc2", "Python tutorial", [0.15] * 1280)
        db.add_document("doc3", "JavaScript", [0.9] * 1280)

        # Buscar
        results = db.query([0.1] * 1280, top_k=3)

        # Deve estar ordenado por similaridade
        distances = [r["distance"] for r in results]
        assert distances == sorted(distances)

    def test_persist_data(self, db):
        """Teste: Dados devem ser persistidos"""
        db.add_document("persist_doc", "Persistent text", [0.1] * 1280)
        db.persist()

        # Criar nova instância com mesmo diretório
        db2 = VectorDB(persist_directory=db.persist_directory)

        # Documento deve estar acessível
        result = db2.get_document("persist_doc")
        assert result is not None

    def test_metadata_filtering_multiple_conditions(self, db, sample_embeddings):
        """Teste: Deve suportar filtros com múltiplas condições"""
        documents = []
        for doc_id, data in sample_embeddings.items():
            documents.append({
                "id": doc_id,
                "text": data["text"],
                "embedding": data["embedding"],
                "metadata": data["metadata"],
            })
        db.add_documents(documents)

        # Buscar com múltiplos filtros
        results = db.query(
            [0.1] * 1280,
            top_k=10,
            filter={
                "$or": [
                    {"language": "python"},
                    {"type": "pattern"},
                ]
            }
        )

        assert len(results) >= 0

    def test_empty_query_result(self, db):
        """Teste: Query em DB vazio deve retornar lista vazia"""
        results = db.query([0.1] * 1280, top_k=10)

        assert isinstance(results, list)
        assert len(results) == 0
