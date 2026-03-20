"""Tests for decision analyzer."""

import pytest
from datetime import datetime, timedelta
from src.analyzer.models import (
    CommitAuthor,
    ChangePattern,
    ChangeType,
    AnalyzedCommit,
    CommitHistoryAnalysis,
    Decision,
    DecisionType,
)
from src.analyzer.decision_analyzer import DecisionAnalyzer


@pytest.fixture
def sample_commit():
    """Create a sample analyzed commit."""
    author = CommitAuthor(name="Test User", email="test@example.com")
    change = ChangePattern(
        file_count=5,
        added_lines=50,
        removed_lines=10,
        modified_lines=5,
        file_extensions=["py", "md"],
        change_type=ChangeType.FEATURE,
    )
    
    return AnalyzedCommit(
        hash="abc123",
        message="feat(architecture): implement MVC pattern for modularity",
        author=author,
        date=datetime.now(),
        change_pattern=change,
        detected_decisions=[],
        related_commits=[],
        significance_score=0.7,
    )


@pytest.fixture
def breaking_change_commit():
    """Create a commit with breaking change."""
    author = CommitAuthor(name="Dev", email="dev@example.com")
    change = ChangePattern(
        file_count=15,
        added_lines=200,
        removed_lines=150,
        modified_lines=15,
        file_extensions=["py", "java"],
        change_type=ChangeType.BREAKING,
    )
    
    return AnalyzedCommit(
        hash="def456",
        message="feat!: BREAKING CHANGE: redesign API response format\n\nThis changes the response structure.",
        author=author,
        date=datetime.now(),
        change_pattern=change,
        detected_decisions=[],
        related_commits=[],
        significance_score=0.95,
    )


class TestDecisionAnalyzer:
    """Test suite for DecisionAnalyzer."""

    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = DecisionAnalyzer(min_significance=0.5)
        
        assert analyzer.min_significance == 0.5

    def test_extract_decision_name(self, sample_commit):
        """Test extracting decision name from commit."""
        analyzer = DecisionAnalyzer()
        name = analyzer._extract_decision_name(sample_commit)
        
        assert "MVC" in name or "implement" in name

    def test_extract_decision_name_long_message(self):
        """Test extracting name from very long message."""
        author = CommitAuthor(name="User", email="u@test.com")
        commit = AnalyzedCommit(
            hash="x123",
            message="feat: " + "this is a very long subject line that exceeds fifty characters and should be truncated",
            author=author,
            date=datetime.now(),
            change_pattern=ChangePattern(0, 0, 0, 0, [], ChangeType.CHORE),
            detected_decisions=[],
            related_commits=[],
            significance_score=0.5,
        )
        
        analyzer = DecisionAnalyzer()
        name = analyzer._extract_decision_name(commit)
        
        assert len(name) <= 53  # 50 + "..."

    def test_extract_rationale(self, sample_commit):
        """Test extracting rationale from commit body."""
        analyzer = DecisionAnalyzer()
        
        sample_commit.message = "feat: add feature\n\nThis is a detailed rationale"
        rationale = analyzer._extract_rationale(sample_commit)
        
        assert rationale is not None
        assert "rationale" in rationale.lower()

    def test_extract_impact_areas(self, sample_commit):
        """Test extracting impacted areas from files."""
        analyzer = DecisionAnalyzer()
        areas = analyzer._extract_impact_areas(sample_commit)
        
        assert "backend" in areas or "general" in areas
        assert isinstance(areas, list)

    def test_calculate_significance_breaking_change(self, breaking_change_commit):
        """Test significance calculation for breaking changes."""
        analyzer = DecisionAnalyzer()
        score = analyzer._calculate_significance(breaking_change_commit)
        
        assert score > 0.90

    def test_calculate_significance_base(self, sample_commit):
        """Test base significance calculation."""
        analyzer = DecisionAnalyzer()
        score = analyzer._calculate_significance(sample_commit)
        
        assert 0.0 <= score <= 1.0
        assert score >= 0.5  # Base score

    def test_extract_from_commit_architecture(self, sample_commit):
        """Test extracting architecture decisions."""
        analyzer = DecisionAnalyzer()
        decisions = analyzer._extract_from_commit(sample_commit)
        
        assert len(decisions) > 0
        assert any(d.decision_type == DecisionType.ARCHITECTURE for d in decisions)

    def test_extract_from_commit_dependency(self):
        """Test extracting dependency decisions."""
        author = CommitAuthor(name="Dev", email="dev@test.com")
        commit = AnalyzedCommit(
            hash="y789",
            message="feat(deps): upgrade package dependency from 3.x to 4.x",
            author=author,
            date=datetime.now(),
            change_pattern=ChangePattern(2, 10, 10, 2, ["txt", "py"], ChangeType.FEATURE),
            detected_decisions=[],
            related_commits=[],
            significance_score=0.7,
        )
        
        analyzer = DecisionAnalyzer()
        decisions = analyzer._extract_from_commit(commit)
        
        assert len(decisions) > 0
        assert any(d.decision_type == DecisionType.DEPENDENCY for d in decisions)

    def test_analyze_commits(self, sample_commit, breaking_change_commit):
        """Test analyzing multiple commits."""
        analyzer = DecisionAnalyzer(min_significance=0.3)
        decisions = analyzer.analyze_commits([sample_commit, breaking_change_commit])
        
        assert len(decisions) > 0
        assert all(isinstance(d, Decision) for d in decisions)

    def test_count_by_type(self):
        """Test counting decisions by type."""
        decisions = [
            Decision("d1", "desc1", DecisionType.ARCHITECTURE, "h1", datetime.now()),
            Decision("d2", "desc2", DecisionType.ARCHITECTURE, "h2", datetime.now()),
            Decision("d3", "desc3", DecisionType.DEPENDENCY, "h3", datetime.now()),
        ]
        
        analyzer = DecisionAnalyzer()
        counts = analyzer._count_by_type(decisions)
        
        assert counts["architecture"] == 2
        assert counts["dependency"] == 1

    def test_group_by_period(self):
        """Test grouping decisions by time period."""
        now = datetime.now()
        decisions = [
            Decision("d1", "desc1", DecisionType.ARCHITECTURE, "h1", now),
            Decision("d2", "desc2", DecisionType.DEPENDENCY, "h2", now + timedelta(days=30)),
        ]
        
        analyzer = DecisionAnalyzer()
        periods = analyzer._group_by_period(decisions)
        
        assert len(periods) == 2 or len(periods) == 1  # Might be same month
        assert all(isinstance(names, list) for names in periods.values())

    def test_calculate_frequency(self):
        """Test calculating decision frequency."""
        decisions = [
            Decision("d1", "desc1", DecisionType.ARCHITECTURE, "h1", datetime.now()),
            Decision("d2", "desc2", DecisionType.DEPENDENCY, "h2", datetime.now()),
        ]
        
        analyzer = DecisionAnalyzer()
        frequency = analyzer._calculate_frequency(decisions, 20)
        
        assert frequency == 2 / 20
        assert 0.0 <= frequency <= 1.0

    def test_calculate_frequency_zero_commits(self):
        """Test frequency with zero commits."""
        analyzer = DecisionAnalyzer()
        frequency = analyzer._calculate_frequency([], 0)
        
        assert frequency == 0.0

    def test_find_most_impacted(self):
        """Test finding most impacted areas."""
        decisions = [
            Decision("d1", "desc1", DecisionType.ARCHITECTURE, "h1", datetime.now(),
                    impact_areas=["backend", "database"]),
            Decision("d2", "desc2", DecisionType.DEPENDENCY, "h2", datetime.now(),
                    impact_areas=["backend", "frontend"]),
            Decision("d3", "desc3", DecisionType.PATTERN, "h3", datetime.now(),
                    impact_areas=["backend"]),
        ]
        
        analyzer = DecisionAnalyzer()
        areas = analyzer._find_most_impacted(decisions)
        
        assert "backend" in areas
        assert len(areas) <= 5

    def test_detect_decision_patterns(self):
        """Test detecting patterns in decisions."""
        decisions = [
            Decision("d1", "desc1", DecisionType.ARCHITECTURE, "h1", datetime.now()),
            Decision("d2", "desc2", DecisionType.ARCHITECTURE, "h2", datetime.now()),
            Decision("d3", "desc3", DecisionType.DEPENDENCY, "h3", datetime.now()),
        ]
        
        analysis = CommitHistoryAnalysis(
            repository_name="test-repo",
            total_commits=30,
            date_range_start=datetime.now(),
            date_range_end=datetime.now(),
            duration_days=30,
            contributors=[],
            analyzed_commits=[],
            decisions=decisions,
            evolution_phases=[],
            commit_patterns={},
        )
        
        analyzer = DecisionAnalyzer()
        patterns = analyzer.detect_decision_patterns(analysis)
        
        assert patterns["total_decisions"] == 3
        assert patterns["by_type"]["architecture"] == 2
        assert patterns["by_type"]["dependency"] == 1
        assert 0.0 <= patterns["decision_frequency"] <= 1.0

    def test_min_significance_filtering(self):
        """Test filtering by minimum significance."""
        author = CommitAuthor(name="Dev", email="dev@test.com")
        low_sig_commit = AnalyzedCommit(
            hash="z999",
            message="fix: typo in comment",
            author=author,
            date=datetime.now(),
            change_pattern=ChangePattern(1, 1, 0, 1, ["md"], ChangeType.CHORE),
            detected_decisions=[],
            related_commits=[],
            significance_score=0.2,
        )
        
        # Low threshold should include it
        analyzer_low = DecisionAnalyzer(min_significance=0.1)
        decisions_low = analyzer_low.analyze_commits([low_sig_commit])
        
        # High threshold should exclude it
        analyzer_high = DecisionAnalyzer(min_significance=0.9)
        decisions_high = analyzer_high.analyze_commits([low_sig_commit])
        
        assert len(decisions_low) >= len(decisions_high)
