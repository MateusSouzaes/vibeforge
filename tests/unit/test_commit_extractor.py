"""
Testes unitários para CommitExtractor
Responsável por: Extrair commits dos repositórios
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from src.crawler.commit_extractor import CommitExtractor


class TestCommitExtractor:
    """Testes para extração de histórico de commits"""

    @pytest.fixture
    def extractor(self):
        """Instancia CommitExtractor para testes"""
        return CommitExtractor()

    @pytest.fixture
    def mock_repo_path(self, tmp_path):
        """Cria diretório temporário simulando um repositório"""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()
        git_dir = repo_dir / ".git"
        git_dir.mkdir()
        return repo_dir

    def test_initialization(self, extractor):
        """Teste: CommitExtractor deve inicializar corretamente"""
        assert extractor is not None
        assert hasattr(extractor, "extract_commits")

    @patch("subprocess.run")
    def test_extract_commits_success(self, mock_subprocess, extractor, mock_repo_path):
        """Teste: Deve extrair commits com sucesso"""
        mock_output = """d1a2b3c commit message 1 2024-01-15 John Doe
e2f3g4h commit message 2 2024-01-14 Jane Smith
f3g4h5i commit message 3 2024-01-13 Bob Johnson"""

        mock_subprocess.return_value = Mock(
            stdout=mock_output.encode(), returncode=0
        )

        commits = extractor.extract_commits(str(mock_repo_path))

        assert len(commits) == 3
        assert commits[0]["hash"] == "d1a2b3c"
        assert commits[0]["message"] == "commit message 1"

    @patch("subprocess.run")
    def test_extract_commits_empty_repo(self, mock_subprocess, extractor, mock_repo_path):
        """Teste: Deve retornar lista vazia para repositório sem commits"""
        mock_subprocess.return_value = Mock(stdout=b"", returncode=0)

        commits = extractor.extract_commits(str(mock_repo_path))

        assert commits == []

    @patch("subprocess.run")
    def test_extract_commits_git_error(self, mock_subprocess, extractor, mock_repo_path):
        """Teste: Deve lançar erro quando git log falha"""
        mock_subprocess.return_value = Mock(returncode=128)

        with pytest.raises(Exception):
            extractor.extract_commits(str(mock_repo_path))

    def test_parse_commit_line_valid(self, extractor):
        """Teste: Deve fazer parse de linha de commit válida"""
        line = "abc123 Fix bug in login 2024-01-15 John Doe"

        commit = extractor.parse_commit_line(line)

        assert commit["hash"] == "abc123"
        assert commit["message"] == "Fix bug in login"
        assert commit["author"] == "John Doe"
        assert commit["date"] == "2024-01-15"

    def test_parse_commit_line_multiword_message(self, extractor):
        """Teste: Deve fazer parse de commit com mensagem longa"""
        line = "def456 Fix critical bug in authentication module 2024-01-14 Jane Smith"

        commit = extractor.parse_commit_line(line)

        assert commit["hash"] == "def456"
        assert commit["message"] == "Fix critical bug in authentication module"

    def test_parse_commit_line_invalid(self, extractor):
        """Teste: Deve retornar None para linha inválida"""
        invalid_lines = [
            "invalid",
            "",
            "onlyoneword",
        ]

        for line in invalid_lines:
            commit = extractor.parse_commit_line(line)
            assert commit is None

    @patch("subprocess.run")
    def test_extract_commits_with_filters(self, mock_subprocess, extractor, mock_repo_path):
        """Teste: Deve filtrar commits por autor"""
        mock_output = """d1a2b3c commit 1 2024-01-15 John Doe
e2f3g4h commit 2 2024-01-14 Jane Smith
f3g4h5i commit 3 2024-01-13 John Doe"""

        mock_subprocess.return_value = Mock(
            stdout=mock_output.encode(), returncode=0
        )

        commits = extractor.extract_commits(str(mock_repo_path), author="John Doe")

        assert len(commits) == 2

    @patch("subprocess.run")
    def test_extract_commits_with_date_range(self, mock_subprocess, extractor, mock_repo_path):
        """Teste: Deve filtrar commits por intervalo de datas"""
        mock_output = """d1a2b3c commit 1 2024-01-15 John Doe
e2f3g4h commit 2 2024-01-14 Jane Smith"""

        mock_subprocess.return_value = Mock(
            stdout=mock_output.encode(), returncode=0
        )

        commits = extractor.extract_commits(
            str(mock_repo_path),
            since="2024-01-14",
            until="2024-01-15"
        )

        assert len(commits) >= 1

    def test_validate_commit_hash(self, extractor):
        """Teste: Deve validar hash de commit"""
        valid_hashes = [
            "abc123def456",
            "1234567890abcdef",
            "a" * 40,
        ]

        for hash_val in valid_hashes:
            assert extractor.validate_commit_hash(hash_val) is True

    def test_validate_commit_hash_invalid(self, extractor):
        """Teste: Deve rejeitar hash inválido"""
        invalid_hashes = [
            "",
            "toolong" + "a" * 100,
            "xyz",
            "not-a-hash!",
        ]

        for hash_val in invalid_hashes:
            assert extractor.validate_commit_hash(hash_val) is False

    @patch("subprocess.run")
    def test_get_commit_diff(self, mock_subprocess, extractor, mock_repo_path):
        """Teste: Deve obter diff de um commit"""
        mock_diff = """diff --git a/file.py b/file.py
index 1234567..abcdefg 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,3 @@
 print("hello")
-print("world")
+print("world!")"""

        mock_subprocess.return_value = Mock(
            stdout=mock_diff.encode(), returncode=0
        )

        diff = extractor.get_commit_diff(str(mock_repo_path), "abc123")

        assert diff is not None
        assert "diff --git" in diff
