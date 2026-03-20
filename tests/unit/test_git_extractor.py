"""Tests for git commit history extraction."""

import pytest
import tempfile
from pathlib import Path
from src.analyzer.commit_extractor import CommitExtractor
from src.analyzer.models import ChangeType


@pytest.fixture
def git_repo():
    """Create a temporary git repository with test commits."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Initialize git repo
        import subprocess
        subprocess.run(
            ["git", "init"],
            cwd=str(repo_path),
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=str(repo_path),
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=str(repo_path),
            capture_output=True,
        )
        
        # Create initial commit
        (repo_path / "README.md").write_text("# Test Project")
        subprocess.run(
            ["git", "add", "README.md"],
            cwd=str(repo_path),
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=str(repo_path),
            capture_output=True,
        )
        
        # Create feature commit
        (repo_path / "feature.py").write_text("def new_feature():\n    pass")
        subprocess.run(
            ["git", "add", "feature.py"],
            cwd=str(repo_path),
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "feat(module): add new feature"],
            cwd=str(repo_path),
            capture_output=True,
        )
        
        yield repo_path


class TestCommitExtractor:
    """Test suite for CommitExtractor."""

    def test_extractor_initialization(self):
        """Test extractor init with valid repository."""
        # Use current repo (this test is running inside vibeforge repo)
        extractor = CommitExtractor("c:\\Desenvolvimento\\Clone-repositorios-git")
        
        assert extractor.repo_path.exists()
        assert (extractor.repo_path / ".git").exists()

    def test_extractor_invalid_path(self):
        """Test extractor with non-git directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError):
                CommitExtractor(tmpdir)

    def test_extract_all_commits(self, git_repo):
        """Test extracting commits from repository."""
        extractor = CommitExtractor(str(git_repo))
        commits = extractor.extract_all_commits()
        
        assert len(commits) >= 2  # At least initial + feature commits
        assert all("hash" in c for c in commits)
        assert all("subject" in c for c in commits)
        assert all("author" in c for c in commits)

    def test_parse_git_log(self, git_repo):
        """Test parsing git log output."""
        extractor = CommitExtractor(str(git_repo))
        
        # Simulate git log output
        log_output = (
            "abc123|Initial commit|Test User|test@example.com|2024-01-15 10:00:00|\n"
            "def456|Add feature|Test User|test@example.com|2024-01-16 11:00:00|"
        )
        
        commits = extractor._parse_git_log(log_output)
        
        assert len(commits) == 2
        assert commits[0]["hash"] == "abc123"
        assert commits[0]["subject"] == "Initial commit"
        assert commits[1]["hash"] == "def456"

    def test_parse_date(self, git_repo):
        """Test date parsing from git format."""
        extractor = CommitExtractor(str(git_repo))
        
        # Test ISO format
        date_str = "2024-01-15 10:30:45 +0100"
        date = extractor._parse_date(date_str)
        
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15

    def test_infer_change_type_test(self, git_repo):
        """Test change type inference for test files."""
        extractor = CommitExtractor(str(git_repo))
        
        change_type = extractor._infer_change_type(10, 5, ["test"])
        
        assert change_type == ChangeType.TEST

    def test_infer_change_type_docs(self, git_repo):
        """Test change type inference for documentation."""
        extractor = CommitExtractor(str(git_repo))
        
        change_type = extractor._infer_change_type(5, 2, ["md"])
        
        assert change_type == ChangeType.DOCS

    def test_infer_change_type_config(self, git_repo):
        """Test change type inference for config files."""
        extractor = CommitExtractor(str(git_repo))
        
        change_type = extractor._infer_change_type(3, 1, ["json"])
        
        assert change_type == ChangeType.CONFIG

    def test_infer_change_type_refactor(self, git_repo):
        """Test change type inference for refactoring."""
        extractor = CommitExtractor(str(git_repo))
        
        # Refactor: many deletions, few additions
        change_type = extractor._infer_change_type(5, 20, ["py"])
        
        assert change_type == ChangeType.REFACTOR

    def test_infer_change_type_feature(self, git_repo):
        """Test change type inference for features."""
        extractor = CommitExtractor(str(git_repo))
        
        # Feature: many additions
        change_type = extractor._infer_change_type(50, 5, ["py"])
        
        assert change_type == ChangeType.FEATURE

    def test_get_contributors(self, git_repo):
        """Test extracting contributors."""
        extractor = CommitExtractor(str(git_repo))
        contributors = extractor.get_contributors()
        
        assert len(contributors) >= 1
        assert contributors[0].name == "Test User"
        assert contributors[0].commits_count >= 2

    def test_get_repo_name(self, git_repo):
        """Test extracting repository name."""
        extractor = CommitExtractor(str(git_repo))
        name = extractor.get_repo_name()
        
        assert name == git_repo.name
        assert len(name) > 0

    def test_extract_history_analysis(self, git_repo):
        """Test extracting complete history analysis."""
        extractor = CommitExtractor(str(git_repo))
        analysis = extractor.extract_history_analysis()
        
        assert analysis.repository_name
        assert analysis.total_commits >= 2
        assert len(analysis.contributors) >= 1
        assert len(analysis.analyzed_commits) >= 2
        assert analysis.duration_days >= 0

    def test_history_date_range(self, git_repo):
        """Test date range in history analysis."""
        extractor = CommitExtractor(str(git_repo))
        analysis = extractor.extract_history_analysis()
        
        assert analysis.date_range_start is not None
        assert analysis.date_range_end is not None
        assert analysis.date_range_start <= analysis.date_range_end
