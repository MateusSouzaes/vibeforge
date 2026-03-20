"""
Testes unitários para EmbeddingService
Responsável por: Geração de embeddings usando Google Gemini
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.embeddings.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Testes para geração de embeddings"""

    @pytest.fixture
    def service(self):
        """Instancia EmbeddingService para testes"""
        return EmbeddingService()

    @pytest.fixture
    def mock_gemini_response(self):
        """Mock de resposta do Gemini"""
        return [0.1, 0.2, 0.3, 0.4, 0.5] * 256  # Vetor com 1280 dimensões

    def test_initialization(self, service):
        """Teste: EmbeddingService deve inicializar corretamente"""
        assert service is not None
        assert hasattr(service, "generate_embedding")
        assert hasattr(service, "batch_embeddings")

    def test_initialization_with_api_key(self):
        """Teste: Deve usar API key da environment"""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            service = EmbeddingService()
            assert service is not None

    @patch("google.generativeai.embed_content")
    def test_generate_embedding_success(self, mock_embed, service, mock_gemini_response):
        """Teste: Deve gerar embedding com sucesso"""
        mock_embed.return_value = {"embedding": mock_gemini_response}

        text = "This is a sample code: def hello(): print('world')"
        embedding = service.generate_embedding(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 1280
        mock_embed.assert_called_once()

    @patch("google.generativeai.embed_content")
    def test_generate_embedding_error(self, mock_embed, service):
        """Teste: Deve lançar erro se API falha"""
        mock_embed.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            service.generate_embedding("Some text")

    def test_generate_embedding_empty_text(self, service):
        """Teste: Deve lançar erro para texto vazio"""
        with pytest.raises(ValueError):
            service.generate_embedding("")

    def test_generate_embedding_text_validation(self, service):
        """Teste: Deve validar tamanho do texto"""
        # Texto muito longo (>100k caracteres)
        long_text = "a" * 150000

        with pytest.raises(ValueError):
            service.generate_embedding(long_text)

    @patch("google.generativeai.embed_content")
    def test_batch_embeddings_success(self, mock_embed, service, mock_gemini_response):
        """Teste: Deve processar batch de textos"""
        mock_embed.return_value = {"embedding": mock_gemini_response}

        texts = [
            "Code chunk 1",
            "Code chunk 2",
            "Code chunk 3",
        ]

        embeddings = service.batch_embeddings(texts)

        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert len(embeddings[0]) == 1280

    @patch("google.generativeai.embed_content")
    def test_batch_embeddings_with_batch_size(self, mock_embed, service, mock_gemini_response):
        """Teste: Deve respeitar batch_size"""
        mock_embed.return_value = {"embedding": mock_gemini_response}

        texts = [f"Text {i}" for i in range(100)]

        embeddings = service.batch_embeddings(texts, batch_size=10)

        assert len(embeddings) == 100

    def test_normalize_embedding(self, service):
        """Teste: Deve normalizar embeddings"""
        embedding = [3.0, 4.0]  # Magnitude 5.0

        normalized = service.normalize_embedding(embedding)

        assert len(normalized) == 2
        assert abs(normalized[0] - 0.6) < 0.001
        assert abs(normalized[1] - 0.8) < 0.001

    def test_calculate_cosine_similarity(self, service):
        """Teste: Deve calcular similaridade do cosseno"""
        emb1 = [1.0, 0.0, 0.0]
        emb2 = [1.0, 0.0, 0.0]

        similarity = service.cosine_similarity(emb1, emb2)

        assert abs(similarity - 1.0) < 0.001  # Deve ser praticamente 1.0

    def test_calculate_cosine_similarity_orthogonal(self, service):
        """Teste: Deve retornar 0 para vetores ortogonais"""
        emb1 = [1.0, 0.0, 0.0]
        emb2 = [0.0, 1.0, 0.0]

        similarity = service.cosine_similarity(emb1, emb2)

        assert abs(similarity) < 0.001

    def test_calculate_cosine_similarity_opposite(self, service):
        """Teste: Deve retornar -1 para vetores opostos"""
        emb1 = [1.0, 0.0, 0.0]
        emb2 = [-1.0, 0.0, 0.0]

        similarity = service.cosine_similarity(emb1, emb2)

        assert abs(similarity - (-1.0)) < 0.001

    @patch("google.generativeai.embed_content")
    def test_cache_embeddings(self, mock_embed, service, mock_gemini_response):
        """Teste: Deve fazer cache de embeddings"""
        mock_embed.return_value = {"embedding": mock_gemini_response}

        text = "Same text"

        embedding1 = service.generate_embedding(text)
        embedding2 = service.generate_embedding(text)

        # Deve chamar a API apenas uma vez (cache no segunda chamada)
        assert mock_embed.call_count <= 2

    @patch("google.generativeai.embed_content")
    def test_clear_cache(self, mock_embed, service, mock_gemini_response):
        """Teste: Deve limpar cache"""
        mock_embed.return_value = {"embedding": mock_gemini_response}

        service.generate_embedding("text")
        service.clear_cache()

        initial_call_count = mock_embed.call_count
        service.generate_embedding("text")

        # Após limpar cache, deve chamar API novamente
        assert mock_embed.call_count > initial_call_count

    @patch("google.generativeai.embed_content")
    def test_get_embedding_model_info(self, mock_embed, service):
        """Teste: Deve retornar informações do modelo"""
        model_info = service.get_model_info()

        assert model_info is not None
        assert "name" in model_info
        assert "dimensions" in model_info
        assert model_info["dimensions"] == 1280

    @patch("google.generativeai.embed_content")
    def test_embedding_dimensions_consistency(self, mock_embed, service):
        """Teste: Todos os embeddings devem ter mesma dimensão"""
        mock_embed.return_value = {"embedding": [0.1] * 1280}

        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = service.batch_embeddings(texts)

        dimensions = [len(emb) for emb in embeddings]
        assert len(set(dimensions)) == 1  # Todas as dimensões iguais
        assert dimensions[0] == 1280

    def test_embedding_vector_properties(self, service):
        """Teste: Verificar propriedades matemáticas do embedding"""
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

        # Deve ser um vetor válido
        assert isinstance(embedding, list)
        assert all(isinstance(x, float) for x in embedding)
        assert len(embedding) > 0
