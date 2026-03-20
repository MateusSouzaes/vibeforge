"""Tests for evolution mapper."""

import pytest
from datetime import datetime, timedelta
from src.analyzer.models import (
    CommitAuthor,
    ChangePattern,
    ChangeType,
    AnalyzedCommit,
    CommitHistoryAnalysis,
    EvolutionPhase,
)
from src.analyzer.evolution_mapper import EvolutionMapper


@pytest.fixture
def sample_commits():
    """Create sample commits with time distribution."""
    base_date = datetime(2024, 1, 1)
    commits = []
    
    # Phase 1: Feature development (week 1-2)
    for i in range(5):
        commits.append(AnalyzedCommit(
            hash=f"phase1_{i}",
            message="feat: add new feature",
            author=CommitAuthor("Dev1", "dev1@test.com"),
            date=base_date + timedelta(days=i),
            change_pattern=ChangePattern(
                3, 50, 10, 3, ["py"], ChangeType.FEATURE
            ),
            detected_decisions=[],
            related_commits=[],
            significance_score=0.6,
        ))
    
    # Phase 2: Testing (week 3-4)
    for i in range(4):
        commits.append(AnalyzedCommit(
            hash=f"phase2_{i}",
            message="test: add unit tests",
            author=CommitAuthor("Dev2", "dev2@test.com"),
            date=base_date + timedelta(days=14 + i),
            change_pattern=ChangePattern(
                2, 30, 5, 2, ["test"], ChangeType.TEST
            ),
            detected_decisions=[],
            related_commits=[],
            significance_score=0.5,
        ))
    
    # Phase 3: Bug fixes (week 5-6)
    for i in range(3):
        commits.append(AnalyzedCommit(
            hash=f"phase3_{i}",
            message="fix: resolve critical bug",
            author=CommitAuthor("Dev1", "dev1@test.com"),
            date=base_date + timedelta(days=30 + i),
            change_pattern=ChangePattern(
                1, 20, 15, 1, ["py"], ChangeType.BUGFIX
            ),
            detected_decisions=[],
            related_commits=[],
            significance_score=0.7,
        ))
    
    return commits


@pytest.fixture
def sample_analysis(sample_commits):
    """Create sample history analysis."""
    return CommitHistoryAnalysis(
        repository_name="test-repo",
        total_commits=len(sample_commits),
        date_range_start=sample_commits[0].date,
        date_range_end=sample_commits[-1].date,
        duration_days=33,
        contributors=[
            CommitAuthor("Dev1", "dev1@test.com", commits_count=8),
            CommitAuthor("Dev2", "dev2@test.com", commits_count=4),
        ],
        analyzed_commits=sample_commits,
        decisions=[],
        evolution_phases=[],
        commit_patterns={},
    )


class TestEvolutionMapper:
    """Test suite for EvolutionMapper."""

    def test_mapper_initialization(self):
        """Test mapper initialization."""
        mapper = EvolutionMapper(phase_detection_days=30)
        
        assert mapper.phase_detection_days == 30

    def test_map_phases(self, sample_analysis):
        """Test mapping evolution phases."""
        mapper = EvolutionMapper(phase_detection_days=20)
        phases = mapper.map_phases(sample_analysis)
        
        assert len(phases) > 0
        assert all(isinstance(p, EvolutionPhase) for p in phases)

    def test_phase_attributes(self, sample_analysis):
        """Test phase has all required attributes."""
        mapper = EvolutionMapper(phase_detection_days=20)
        phases = mapper.map_phases(sample_analysis)
        
        for phase in phases:
            assert phase.name is not None
            assert phase.start_date is not None
            assert phase.end_date is not None
            assert phase.duration_days > 0
            assert phase.commit_count > 0
            assert phase.primary_focus is not None
            assert isinstance(phase.contributors, list)

    def test_determine_focus_feature(self):
        """Test determining focus for feature commits."""
        mapper = EvolutionMapper()
        
        author = CommitAuthor("Dev", "dev@test.com")
        commits = [
            AnalyzedCommit(
                hash=f"h{i}",
                message="feat: add feature",
                author=author,
                date=datetime.now(),
                change_pattern=ChangePattern(
                    1, 30, 5, 1, ["py"], ChangeType.FEATURE
                ),
                detected_decisions=[],
                related_commits=[],
                significance_score=0.5,
            )
            for i in range(3)
        ]
        
        focus = mapper._determine_focus(commits)
        
        assert "feature" in focus.lower()

    def test_generate_phase_name(self):
        """Test phase name generation."""
        mapper = EvolutionMapper()
        
        name = mapper._generate_phase_name("feature development", datetime(2024, 3, 15))
        
        assert "Feature" in name or "feature" in name.lower()
        assert "Mar" in name or "2024" in name

    def test_identify_major_transitions(self, sample_analysis):
        """Test identifying major transitions."""
        mapper = EvolutionMapper(phase_detection_days=20)
        phases = mapper.map_phases(sample_analysis)
        transitions = mapper.identify_major_transitions(phases)
        
        assert isinstance(transitions, list)
        if transitions:
            assert all("from_phase" in t for t in transitions)
            assert all("to_phase" in t for t in transitions)

    def test_estimate_maturity_embryonic(self):
        """Test maturity estimation for small projects."""
        mapper = EvolutionMapper()
        
        analysis = CommitHistoryAnalysis(
            repository_name="tiny",
            total_commits=5,
            date_range_start=datetime.now(),
            date_range_end=datetime.now(),
            duration_days=1,
            contributors=[],
            analyzed_commits=[],
            decisions=[],
            evolution_phases=[],
            commit_patterns={},
        )
        
        maturity = mapper.estimate_maturity(analysis)
        
        assert "Embryonic" in maturity or "Early" in maturity

    def test_estimate_maturity_mature(self):
        """Test maturity estimation for large projects."""
        mapper = EvolutionMapper()
        
        analysis = CommitHistoryAnalysis(
            repository_name="big",
            total_commits=1500,
            date_range_start=datetime.now(),
            date_range_end=datetime.now(),
            duration_days=1,
            contributors=[],
            analyzed_commits=[],
            decisions=[],
            evolution_phases=[],
            commit_patterns={},
        )
        
        maturity = mapper.estimate_maturity(analysis)
        
        assert "Mature" in maturity or "Production" in maturity

    def test_calculate_velocity_trends(self, sample_analysis):
        """Test velocity calculation."""
        mapper = EvolutionMapper(phase_detection_days=20)
        phases = mapper.map_phases(sample_analysis)
        trends = mapper.calculate_velocity_trends(phases)
        
        assert len(trends) > 0
        for trend in trends:
            assert "phase" in trend
            assert "velocity" in trend
            assert 0 <= trend["velocity"]

    def test_identify_critical_periods(self, sample_analysis):
        """Test identifying critical periods."""
        mapper = EvolutionMapper()
        critical = mapper.identify_critical_periods(sample_analysis)
        
        assert isinstance(critical, list)
        if critical:
            for period in critical:
                assert "period" in period
                assert "commit_count" in period

    def test_phase_to_dict(self):
        """Test converting phase to dictionary."""
        phase = EvolutionPhase(
            name="Test Phase",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=10),
            duration_days=10,
            commit_count=5,
            primary_focus="testing",
            key_decisions=["decision1"],
            contributors=["User1"],
        )
        
        mapper = EvolutionMapper()
        phase_dict = mapper._phase_to_dict(phase)
        
        assert phase_dict["name"] == "Test Phase"
        assert "start_date" in phase_dict
        assert "duration_days" in phase_dict

    def test_generate_evolution_summary(self, sample_analysis):
        """Test generating evolution summary."""
        mapper = EvolutionMapper(phase_detection_days=20)
        summary = mapper.generate_evolution_summary(sample_analysis)
        
        assert "total_phases" in summary
        assert "phases" in summary
        assert "major_transitions" in summary
        assert "project_maturity" in summary
        assert summary["total_phases"] > 0

    def test_empty_analysis(self):
        """Test handling empty analysis."""
        mapper = EvolutionMapper()
        
        analysis = CommitHistoryAnalysis(
            repository_name="empty",
            total_commits=0,
            date_range_start=datetime.now(),
            date_range_end=datetime.now(),
            duration_days=0,
            contributors=[],
            analyzed_commits=[],
            decisions=[],
            evolution_phases=[],
            commit_patterns={},
        )
        
        phases = mapper.map_phases(analysis)
        
        assert phases == []

    def test_single_commit(self):
        """Test handling single commit."""
        mapper = EvolutionMapper()
        
        commit = AnalyzedCommit(
            hash="single",
            message="initial commit",
            author=CommitAuthor("User", "u@test.com"),
            date=datetime.now(),
            change_pattern=ChangePattern(1, 10, 0, 1, ["py"], ChangeType.CHORE),
            detected_decisions=[],
            related_commits=[],
            significance_score=0.5,
        )
        
        analysis = CommitHistoryAnalysis(
            repository_name="single-commit",
            total_commits=1,
            date_range_start=commit.date,
            date_range_end=commit.date,
            duration_days=1,
            contributors=[commit.author],
            analyzed_commits=[commit],
            decisions=[],
            evolution_phases=[],
            commit_patterns={},
        )
        
        phases = mapper.map_phases(analysis)
        
        # Single commit shouldn't form a phase
        assert len(phases) == 0
