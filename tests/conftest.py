"""
Configurações compartilhadas para testes
Fixtures e configurações globais
"""

import pytest
import os
from dotenv import load_dotenv
from pathlib import Path


# Carregar variáveis de ambiente para testes
load_dotenv(Path(__file__).parent.parent / ".env.test")


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """Diretório temporário para dados de teste"""
    return tmp_path_factory.mktemp("test_data")


@pytest.fixture(scope="session")
def test_config():
    """Configuração de teste"""
    return {
        "database": {
            "provider": "sqlite",
            "path": ":memory:",
        },
        "gemini": {
            "api_key": os.getenv("GEMINI_API_KEY", "test-key"),
            "model": "embedding-001",
        },
        "chroma": {
            "persist_directory": None,  # Em memória
        }
    }


@pytest.fixture(scope="function")
def clean_env():
    """Limpar e restaurar variáveis de ambiente"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset de mocks antes de cada teste"""
    from unittest.mock import patch
    with patch("os.environ", {"TESTING": "true", "USER": "testuser"}):
        yield


@pytest.fixture
def sample_embeddings():
    """Embeddings de exemplo para todos os testes"""
    return [0.1] * 1280  # Dimensão padrão do Gemini


@pytest.fixture
def sample_code_snippets():
    """Snippets de código para análise"""
    return {
        "python": {
            "simple": "print('hello')",
            "function": "def add(a, b):\n    return a + b",
            "class": "class MyClass:\n    def method(self):\n        pass",
        },
        "javascript": {
            "simple": "console.log('hello')",
            "function": "function add(a, b) { return a + b; }",
            "class": "class MyClass { method() {} }",
        },
    }


@pytest.fixture
def mock_api_responses():
    """Respostas mockadas de APIs"""
    return {
        "github_user_repos": [
            {"name": "repo1", "clone_url": "https://github.com/user/repo1.git"},
            {"name": "repo2", "clone_url": "https://github.com/user/repo2.git"},
        ],
        "gemini_embedding": [0.1] * 1280,
        "git_log": """abc123 Fix bug 2024-01-15 John Doe
def456 Add feature 2024-01-14 Jane Smith""",
    }


# Configurar pytest
def pytest_configure(config):
    """Configuração inicial do pytest"""
    config.addinivalue_line(
        "markers", "unit: marca um teste como unitário"
    )
    config.addinivalue_line(
        "markers", "integration: marca um teste como de integração"
    )
    config.addinivalue_line(
        "markers", "slow: marca um teste como lento"
    )
    config.addinivalue_line(
        "markers", "requires_api: marca um teste que requer API externa"
    )


# Hooks de pytest
def pytest_collection_modifyitems(config, items):
    """Adicionar markers automaticamente baseado no nome do arquivo"""
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)


def pytest_sessionfinish(session, exitstatus):
    """Limpeza após todos os testes"""
    # Limpar arquivos temporários, etc
    pass
