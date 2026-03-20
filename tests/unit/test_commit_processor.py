"""
Testes unitários para CommitProcessor
Responsável por: Processamento de commits
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from src.processor.commit_processor import CommitProcessor


class TestCommitProcessor:
    """Testes para processamento de commits"""

    @pytest.fixture
    def processor(self):
        """Instancia CommitProcessor para testes"""
        return CommitProcessor()

    @pytest.fixture
    def sample_commits(self):
        """Retorna commits de exemplo para testes"""
        return [
            {
                "hash": "abc123",
                "message": "Fix: Resolve bug in authentication",
                "author": "John Doe",
                "date": "2024-01-15",
                "email": "john@example.com",
            },
            {
                "hash": "def456",
                "message": "Feature: Add new API endpoint",
                "author": "Jane Smith",
                "date": "2024-01-14",
                "email": "jane@example.com",
            },
            {
                "hash": "ghi789",
                "message": "Refactor: Improve code structure",
                "author": "Bob Johnson",
                "date": "2024-01-13",
                "email": "bob@example.com",
            },
        ]

    def test_initialization(self, processor):
        """Teste: CommitProcessor deve inicializar corretamente"""
        assert processor is not None
        assert hasattr(processor, "process_commits")

    def test_process_commits_valid(self, processor, sample_commits):
        """Teste: Deve processar commits válidos"""
        processed = processor.process_commits(sample_commits)

        assert isinstance(processed, list)
        assert len(processed) == 3

        # Verificar primeira entrada
        assert processed[0]["hash"] == "abc123"
        assert "type" in processed[0]  # Deve conter tipo de commit

    def test_extract_commit_type(self, processor):
        """Teste: Deve extrair tipo de commit da mensagem"""
        test_cases = [
            ("Fix: bug in login", "fix"),
            ("Feature: new endpoint", "feature"),
            ("Refactor: improve code", "refactor"),
            ("Docs: update README", "docs"),
            ("Test: add unit tests", "test"),
            ("Regular commit message", "other"),
        ]

        for message, expected_type in test_cases:
            commit_type = processor.extract_commit_type(message)
            assert commit_type == expected_type

    def test_extract_commit_scope(self, processor):
        """Teste: Deve extrair escopo de commit"""
        test_cases = [
            ("Fix(auth): resolve bug", "auth"),
            ("Feature(api): new endpoint", "api"),
            ("Refactor(db): improve queries", "db"),
            ("Regular message", None),
        ]

        for message, expected_scope in test_cases:
            scope = processor.extract_commit_scope(message)
            assert scope == expected_scope

    def test_normalize_commit_message(self, processor):
        """Teste: Deve normalizar mensagem de commit"""
        message = "  Fix:  Resolve   bug  in   login  \n"
        normalized = processor.normalize_message(message)

        assert normalized == "Fix: Resolve bug in login"
        assert "  " not in normalized  # Sem espaços duplos
        assert normalized[0] != " "  # Sem espaço inicial

    def test_enrich_commits_with_stats(self, processor, sample_commits):
        """Teste: Deve enriquecer commits com estatísticas"""
        enriched = processor.enrich_commits(sample_commits)

        assert len(enriched) > 0

        for commit in enriched:
            assert "type" in commit
            assert "normalized_message" in commit
            assert "author_domain" in commit  # Extrair domínio do email

    def test_extract_author_domain(self, processor):
        """Teste: Deve extrair domínio do email do autor"""
        test_cases = [
            ("john@example.com", "example.com"),
            ("jane.smith@company.co.uk", "company.co.uk"),
            ("bob@localhost", "localhost"),
        ]

        for email, expected_domain in test_cases:
            domain = processor.extract_author_domain(email)
            assert domain == expected_domain

    def test_extract_keywords_from_message(self, processor):
        """Teste: Deve extrair keywords de message"""
        message = "Fix critical bug in authentication module for user login"
        keywords = processor.extract_keywords(message)

        assert isinstance(keywords, list)
        assert "bug" in keywords
        assert "authentication" in keywords
        assert len(keywords) > 0

    def test_group_commits_by_type(self, processor, sample_commits):
        """Teste: Deve agrupar commits por tipo"""
        grouped = processor.group_by_type(sample_commits)

        assert isinstance(grouped, dict)
        assert "fix" in grouped
        assert "feature" in grouped

    def test_group_commits_by_author(self, processor, sample_commits):
        """Teste: Deve agrupar commits por autor"""
        grouped = processor.group_by_author(sample_commits)

        assert isinstance(grouped, dict)
        assert "John Doe" in grouped
        assert "Jane Smith" in grouped
        assert len(grouped["John Doe"]) == 1

    def test_calculate_commit_stats(self, processor, sample_commits):
        """Teste: Deve calcular estatísticas de commits"""
        stats = processor.calculate_stats(sample_commits)

        assert stats["total"] == 3
        assert stats["unique_authors"] == 3
        assert isinstance(stats["commits_by_type"], dict)
        assert isinstance(stats["commits_by_author"], dict)

    def test_detect_merge_commit(self, processor):
        """Teste: Deve detectar commits de merge"""
        merge_messages = [
            "Merge branch 'feature' into develop",
            "Merge pull request #123",
            "Merge tag 'v1.0.0'",
        ]

        for message in merge_messages:
            is_merge = processor.is_merge_commit(message)
            assert is_merge is True

    def test_detect_non_merge_commit(self, processor):
        """Teste: Deve identificar commits normais"""
        regular_messages = [
            "Fix bug",
            "Add feature",
            "Refactor code",
        ]

        for message in regular_messages:
            is_merge = processor.is_merge_commit(message)
            assert is_merge is False

    def test_filter_commits_by_date_range(self, processor, sample_commits):
        """Teste: Deve filtrar commits por intervalo de datas"""
        filtered = processor.filter_by_date_range(
            sample_commits,
            since="2024-01-14",
            until="2024-01-15"
        )

        assert len(filtered) == 2

    def test_filter_commits_by_author(self, processor, sample_commits):
        """Teste: Deve filtrar commits por autor"""
        filtered = processor.filter_by_author(sample_commits, "John Doe")

        assert len(filtered) == 1
        assert filtered[0]["author"] == "John Doe"

    def test_commits_with_missing_fields(self, processor):
        """Teste: Deve lidar com commits com campos faltando"""
        incomplete_commits = [
            {"hash": "abc123", "message": "Fix bug"},  # Falta author e date
        ]

        # Não deve lançar erro
        processed = processor.process_commits(incomplete_commits)
        assert processed is not None
