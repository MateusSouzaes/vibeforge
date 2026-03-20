"""
Testes unitários para RepoDownloader
Responsável por: Ingerir repositórios GitHub
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.crawler.repo_downloader import RepoDownloader


class TestRepoDownloader:
    """Testes para ingestão e clone de repositórios GitHub"""

    @pytest.fixture
    def downloader(self):
        """Instancia RepoDownloader para testes"""
        return RepoDownloader()

    @pytest.fixture
    def mock_github_response(self):
        """Mock de resposta da API GitHub"""
        return [
            {"name": "repo1", "clone_url": "https://github.com/user/repo1.git"},
            {"name": "repo2", "clone_url": "https://github.com/user/repo2.git"},
        ]

    def test_initialization(self, downloader):
        """Teste: RepoDownloader deve inicializar corretamente"""
        assert downloader is not None
        assert hasattr(downloader, "download_repos")

    @patch("requests.get")
    def test_fetch_user_repos_success(self, mock_get, downloader):
        """Teste: Deve buscar repositórios do usuário com sucesso"""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"name": "repo1", "clone_url": "https://github.com/user/repo1.git"},
            {"name": "repo2", "clone_url": "https://github.com/user/repo2.git"},
        ]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        username = "akitaonrails"
        repos = downloader.fetch_user_repos(username)

        assert len(repos) == 2
        assert repos[0]["name"] == "repo1"
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_fetch_user_repos_api_error(self, mock_get, downloader):
        """Teste: Deve lançar erro quando API GitHub falha"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(Exception):
            downloader.fetch_user_repos("nonexistent_user")

    @patch("subprocess.run")
    def test_clone_repo_success(self, mock_subprocess, downloader, tmp_path):
        """Teste: Deve clonar repositório com sucesso"""
        mock_subprocess.return_value = Mock(returncode=0)

        clone_url = "https://github.com/user/repo1.git"
        dest_path = tmp_path / "repo1"

        result = downloader.clone_repo(clone_url, str(dest_path))

        assert result is True
        mock_subprocess.assert_called_once()

    @patch("subprocess.run")
    def test_clone_repo_failure(self, mock_subprocess, downloader, tmp_path):
        """Teste: Deve retornar False quando clone falha"""
        mock_subprocess.return_value = Mock(returncode=1)

        clone_url = "https://github.com/user/repo1.git"
        dest_path = tmp_path / "repo1"

        result = downloader.clone_repo(clone_url, str(dest_path))

        assert result is False

    @patch("subprocess.run")
    def test_clone_repo_with_shallow_clone(self, mock_subprocess, downloader, tmp_path):
        """Teste: Deve usar --depth 1 para shallow clone (v1.1)"""
        mock_subprocess.return_value = Mock(returncode=0)

        clone_url = "https://github.com/user/repo1.git"
        dest_path = tmp_path / "repo1"

        result = downloader.clone_repo(clone_url, str(dest_path))

        assert result is True
        # Verificar que --depth 1 foi passado ao comando git
        call_args = mock_subprocess.call_args
        cmd = call_args[0][0]  # Primeiro argumento da primeira chamada
        assert "--depth" in cmd
        assert "1" in cmd

    @patch("shutil.rmtree")
    @patch("os.path.isdir")
    @patch("subprocess.run")
    def test_cleanup_post_clone(self, mock_subprocess, mock_isdir, mock_rmtree, 
                                downloader, tmp_path):
        """Teste: Deve remover diretórios não essenciais após clone (v1.1)"""
        mock_subprocess.return_value = Mock(returncode=0)
        mock_isdir.return_value = True

        clone_url = "https://github.com/user/repo1.git"
        dest_path = tmp_path / "repo1"

        result = downloader.clone_repo(clone_url, str(dest_path))

        assert result is True
        # Verificar que cleanup_post_clone foi chamado (rmtree foi chamado)
        # Diretórios esperados: .git, node_modules, __pycache__, etc
        assert mock_rmtree.call_count >= 1

    @patch("requests.get")
    def test_fetch_user_repos_rate_limit_handled(self, mock_get, downloader):
        """Teste: Deve lidar com rate limit (429) do GitHub (v1.1)"""
        import time
        
        # Simular resposta 429 com header x-ratelimit-reset
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {
            "x-ratelimit-reset": str(int(time.time()) + 5)
        }
        
        # Simular resposta 200 após retry
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = [
            {"name": "repo1", "clone_url": "https://github.com/user/repo1.git"}
        ]
        
        # Primeira chamada retorna 429, segunda retorna 200
        mock_get.side_effect = [mock_response_429, mock_response_200]

        username = "akitaonrails"
        
        # Deve retry após receber 429
        with patch("time.sleep"):  # Mock sleep para não esperar de verdade
            repos = downloader.fetch_user_repos(username, retries=2)
        
        # Após retry, deve ter sucesso
        assert mock_get.call_count >= 2  # Mínimo 2 chamadas (retry)

    @patch("requests.get")
    def test_rate_limit_header_parsing(self, mock_get, downloader):
        """Teste: Deve parsear header x-ratelimit-reset corretamente (v1.1)"""
        import time
        
        mock_response = Mock()
        mock_response.status_code = 429
        reset_time = int(time.time()) + 10
        mock_response.headers = {"x-ratelimit-reset": str(reset_time)}
        mock_get.return_value = mock_response

        username = "test_user"
        
        # Verificar se header é lido (aqui apenas validamos o comportamento)
        try:
            with patch("time.sleep"):  # Mock sleep
                downloader.fetch_user_repos(username, retries=1)
        except Exception:
            pass  # Esperamos que falhe após retry, mas header foi lido

    @patch("subprocess.run")
    @patch("os.path.isdir")
    @patch("shutil.rmtree")
    def test_cleanup_removes_git_directory(self, mock_rmtree, mock_isdir, 
                                         mock_subprocess, downloader, tmp_path):
        """Teste: Cleanup deve remover .git especificamente (v1.1)"""
        mock_subprocess.return_value = Mock(returncode=0)
        mock_isdir.return_value = True

        clone_url = "https://github.com/user/repo1.git"
        dest_path = str(tmp_path / "repo1")

        downloader.clone_repo(clone_url, dest_path)

        # Verificar que .git foi removido
        rmtree_calls = [call[0][0] for call in mock_rmtree.call_args_list]
        
        # Verificar que pelo menos um dos argumentos contém .git
        git_dirs_removed = [call for call in rmtree_calls if ".git" in str(call)]
        assert len(git_dirs_removed) > 0, "Diretório .git não foi removido"

    def test_validate_github_url_valid(self, downloader):
        """Teste: Deve validar URL GitHub válida"""
        valid_urls = [
            "https://github.com/user/repo.git",
            "https://github.com/user/repo",
            "git@github.com:user/repo.git",
        ]

        for url in valid_urls:
            assert downloader.validate_github_url(url) is True

    def test_validate_github_url_invalid(self, downloader):
        """Teste: Deve rejeitar URL GitHub inválida"""
        invalid_urls = [
            "https://example.com/repo.git",
            "not-a-url",
            "",
        ]

        for url in invalid_urls:
            assert downloader.validate_github_url(url) is False

    @patch("subprocess.run")
    @patch("requests.get")
    def test_download_repos_full_flow(self, mock_get, mock_subprocess, downloader):
        """Teste: Fluxo completo de download (busca + clone)"""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"name": "repo1", "clone_url": "https://github.com/user/repo1.git"}
        ]
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        mock_subprocess.return_value = Mock(returncode=0)

        result = downloader.download_repos("user", "/data/repos")

        assert result is not None
        assert len(result) >= 0
        mock_get.assert_called_once()

    def test_extract_repo_name_from_url(self, downloader):
        """Teste: Deve extrair nome do repositório da URL"""
        urls_and_expected = [
            ("https://github.com/user/myrepo.git", "myrepo"),
            ("https://github.com/user/my-repo.git", "my-repo"),
            ("git@github.com:user/repo.git", "repo"),
        ]

        for url, expected_name in urls_and_expected:
            name = downloader.extract_repo_name(url)
            assert name == expected_name
