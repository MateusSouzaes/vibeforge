"""Tests for UC-006 roadmap generation."""

import pytest
import tempfile
import os
from pathlib import Path

from src.roadmap.models import (
    RoadmapPhase, TechCategory, Recommendation, ProjectContext,
    ArchitecturalRecommendation, BestPractice, RoadmapConfig,
    ArchitecturalRoadmap, ProjectAnalysisResult
)
from src.roadmap.analyzer import ArchitectureAnalyzer
from src.roadmap.roadmap_generator import RoadmapGenerator


class TestRoadmapPhase:
    """Test RoadmapPhase enum."""
    
    def test_phase_values(self):
        """Test all phase values exist."""
        assert RoadmapPhase.FOUNDATION.value == "foundation"
        assert RoadmapPhase.MVP.value == "mvp"
        assert RoadmapPhase.OPTIMIZATION.value == "optimization"
        assert RoadmapPhase.SCALING.value == "scaling"
        assert RoadmapPhase.MATURITY.value == "maturity"


class TestTechCategory:
    """Test TechCategory enum."""
    
    def test_category_values(self):
        """Test all category values exist."""
        assert TechCategory.ARCHITECTURE.value == "architecture"
        assert TechCategory.TESTING.value == "testing"
        assert TechCategory.DOCUMENTATION.value == "documentation"
        assert TechCategory.DEPLOYMENT.value == "deployment"
        assert TechCategory.SECURITY.value == "security"


class TestProjectContext:
    """Test ProjectContext model."""
    
    def test_create_context(self):
        """Create a project context."""
        context = ProjectContext(
            project_name="test-project",
            repository_path="/path/to/repo",
            primary_language="python",
            detected_frameworks=["django"],
            total_code_files=50,
            total_test_files=45,
            test_coverage=0.85,
            code_complexity=6.5,
            technical_debt=0.2,
            project_age_days=365,
            contributors_count=5,
            last_commit_age_days=2,
        )
        
        assert context.project_name == "test-project"
        assert context.primary_language == "python"
        assert len(context.detected_frameworks) == 1
        assert context.total_code_files == 50
        assert context.test_coverage == 0.85
    
    def test_context_with_metadata(self):
        """Create context with metadata."""
        context = ProjectContext(
            project_name="test",
            repository_path="/path",
            primary_language="python",
            metadata={"custom_key": "custom_value"}
        )
        assert context.metadata["custom_key"] == "custom_value"


class TestArchitecturalRecommendation:
    """Test ArchitecturalRecommendation model."""
    
    def test_create_recommendation(self):
        """Create a recommendation."""
        rec = ArchitecturalRecommendation(
            title="Add Tests",
            category=TechCategory.TESTING,
            recommendation_type=Recommendation.IMPROVE,
            description="Add missing tests",
            why="Increase reliability",
            impact="Better code quality",
            effort="medium",
            priority=8,
            confidence_score=0.9,
        )
        
        assert rec.title == "Add Tests"
        assert rec.priority == 8
        assert rec.confidence_score == 0.9
    
    def test_invalid_confidence_score(self):
        """Test invalid confidence score."""
        with pytest.raises(ValueError):
            ArchitecturalRecommendation(
                title="Test",
                category=TechCategory.TESTING,
                recommendation_type=Recommendation.IMPROVE,
                description="Test",
                why="Test",
                impact="Test",
                effort="low",
                priority=5,
                confidence_score=1.5,  # Invalid
            )
    
    def test_invalid_priority(self):
        """Test invalid priority."""
        with pytest.raises(ValueError):
            ArchitecturalRecommendation(
                title="Test",
                category=TechCategory.TESTING,
                recommendation_type=Recommendation.IMPROVE,
                description="Test",
                why="Test",
                impact="Test",
                effort="low",
                priority=15,  # Invalid
                confidence_score=0.8,
            )


class TestBestPractice:
    """Test BestPractice model."""
    
    def test_create_best_practice(self):
        """Create a best practice."""
        practice = BestPractice(
            title="Layered Architecture",
            category=TechCategory.ARCHITECTURE,
            description="Organize code into layers",
            benefits=["Testability", "Maintainability"],
            is_currently_applied=False,
        )
        
        assert practice.title == "Layered Architecture"
        assert len(practice.benefits) == 2
        assert practice.is_currently_applied is False


class TestRoadmapConfig:
    """Test RoadmapConfig model."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = RoadmapConfig()
        
        assert config.include_patterns is True
        assert config.include_best_practices is True
        assert config.max_recommendations == 20
        assert config.min_confidence_threshold == 0.6
        assert config.phases_to_generate == 4
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = RoadmapConfig(
            max_recommendations=10,
            min_confidence_threshold=0.8,
            phases_to_generate=2,
        )
        
        assert config.max_recommendations == 10
        assert config.min_confidence_threshold == 0.8
        assert config.phases_to_generate == 2
    
    def test_invalid_config(self):
        """Test invalid configuration."""
        config = RoadmapConfig(max_recommendations=0)
        with pytest.raises(ValueError):
            config.validate()
    
    def test_invalid_confidence_threshold(self):
        """Test invalid confidence threshold."""
        config = RoadmapConfig(min_confidence_threshold=1.5)
        with pytest.raises(ValueError):
            config.validate()


class TestProjectAnalysisResult:
    """Test ProjectAnalysisResult model."""
    
    def test_create_analysis(self):
        """Create an analysis result."""
        context = ProjectContext(
            project_name="test",
            repository_path="/path",
            primary_language="python",
        )
        
        analysis = ProjectAnalysisResult(
            context=context,
            architecture_score=7.5,
            test_score=6.0,
            documentation_score=5.0,
            security_score=7.0,
            maintainability_score=6.5,
            scalability_score=5.5,
        )
        
        assert analysis.architecture_score == 7.5
        assert analysis.test_score == 6.0


class TestArchitectureAnalyzer:
    """Test ArchitectureAnalyzer."""
    
    def test_score_architecture(self):
        """Test architecture scoring."""
        analyzer = ArchitectureAnalyzer()
        
        context = ProjectContext(
            project_name="test",
            repository_path="/path",
            primary_language="python",
            detected_frameworks=["django"],
            code_complexity=6.0,
        )
        
        score = analyzer._score_architecture(context)
        assert 1.0 <= score <= 10.0
    
    def test_score_tests(self):
        """Test test scoring."""
        analyzer = ArchitectureAnalyzer()
        
        context_no_tests = ProjectContext(
            project_name="test",
            repository_path="/path",
            primary_language="python",
            total_test_files=0,
            test_coverage=0.0,
        )
        
        score = analyzer._score_tests(context_no_tests)
        assert score == 2.0
    
    def test_score_maintainability(self):
        """Test maintainability scoring."""
        analyzer = ArchitectureAnalyzer()
        
        context = ProjectContext(
            project_name="test",
            repository_path="/path",
            primary_language="python",
            code_complexity=7.0,
            last_commit_age_days=3,
        )
        
        score = analyzer._score_maintainability(context)
        assert 1.0 <= score <= 10.0
    
    def test_detect_no_tests_pattern(self):
        """Detect missing test pattern."""
        analyzer = ArchitectureAnalyzer()
        
        context = ProjectContext(
            project_name="test",
            repository_path="/path",
            primary_language="python",
            total_test_files=0,
            test_coverage=0.0,
        )
        
        recs = analyzer.detect_anti_patterns([], context)
        
        # Should have at least 2 recommendations (low coverage + no tests)
        assert len(recs) >= 2
        titles = [r.title for r in recs]
        assert any("test" in t.lower() for t in titles)
    
    def test_detect_high_complexity_pattern(self):
        """Detect high complexity pattern."""
        analyzer = ArchitectureAnalyzer()
        
        context = ProjectContext(
            project_name="test",
            repository_path="/path",
            primary_language="python",
            code_complexity=20.0,  # Very high
            total_test_files=5,
            test_coverage=0.5,
        )
        
        recs = analyzer.detect_anti_patterns([], context)
        
        titles = [r.title for r in recs]
        assert any("god" in t.lower() or "complexity" in t.lower() for t in titles)
    
    def test_suggest_best_practices(self):
        """Test suggesting best practices."""
        analyzer = ArchitectureAnalyzer()
        
        context = ProjectContext(
            project_name="test",
            repository_path="/path",
            primary_language="python",
            total_code_files=100,
            code_complexity=10.0,
            test_coverage=0.5,
        )
        analysis = ProjectAnalysisResult(context=context)
        
        practices = analyzer.suggest_best_practices(context, analysis)
        
        assert len(practices) > 0
        assert all(isinstance(p, BestPractice) for p in practices)
    
    def test_calculate_technical_debt(self):
        """Test technical debt calculation."""
        analyzer = ArchitectureAnalyzer()
        
        context = ProjectContext(
            project_name="test",
            repository_path="/path",
            primary_language="python",
            code_complexity=15.0,
            test_coverage=0.2,
            total_test_files=0,
        )
        
        debt = analyzer.calculate_technical_debt(context)
        
        assert 0.0 <= debt <= 1.0
        assert debt > 0.5  # High debt for this context


class TestRoadmapGenerator:
    """Test RoadmapGenerator."""
    
    def test_create_generator(self):
        """Create a roadmap generator."""
        gen = RoadmapGenerator()
        assert gen is not None
        assert gen.architecture_analyzer is not None
    
    def test_detect_primary_language_python(self):
        """Detect Python as primary language."""
        gen = RoadmapGenerator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some Python files
            Path(tmpdir, "main.py").write_text("print('hello')")
            Path(tmpdir, "utils.py").write_text("def util():\n    pass")
            
            lang = gen._detect_primary_language(tmpdir)
            assert lang == "python"
    
    def test_detect_frameworks_python(self):
        """Detect Python frameworks."""
        gen = RoadmapGenerator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create requirements.txt
            Path(tmpdir, "requirements.txt").write_text(
                "django==4.0\nrequests==2.28.0"
            )
            
            frameworks = gen._detect_frameworks(tmpdir)
            assert "django" in frameworks
    
    def test_estimate_test_coverage(self):
        """Test coverage estimation."""
        gen = RoadmapGenerator()
        
        coverage = gen._estimate_test_coverage(10, 50)
        assert 0.0 <= coverage <= 1.0
        
        # If 1 test per code file, should be ~0.16 (1/5 * 0.8)
        coverage = gen._estimate_test_coverage(1, 5)
        assert coverage > 0.0
    
    def test_estimate_complexity(self):
        """Test complexity estimation."""
        gen = RoadmapGenerator()
        
        assert gen._estimate_complexity(5) < gen._estimate_complexity(100)
        assert gen._estimate_complexity(200) > gen._estimate_complexity(50)
    
    def test_detect_frameworks_with_package_json(self):
        """Detect frameworks from package.json."""
        gen = RoadmapGenerator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            package_json = """{
                "dependencies": {
                    "react": "^18.0.0",
                    "express": "^4.18.0"
                }
            }"""
            Path(tmpdir, "package.json").write_text(package_json)
            
            frameworks = gen._detect_frameworks(tmpdir)
            assert "react" in frameworks or "express" in frameworks
    
    def test_create_project_context(self):
        """Test project context creation."""
        gen = RoadmapGenerator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some files
            Path(tmpdir, "main.py").write_text("print('hello')")
            Path(tmpdir, "test_main.py").write_text("def test(): pass")
            
            context = gen._build_project_context(tmpdir)
            
            assert context.project_name == os.path.basename(tmpdir)
            assert context.total_code_files >= 1
            assert context.total_test_files >= 1
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        gen = RoadmapGenerator()
        
        context = ProjectContext(
            project_name="test",
            repository_path="/path",
            primary_language="python",
            test_coverage=0.3,
            total_test_files=0,
        )
        analysis = ProjectAnalysisResult(context=context)
        config = RoadmapConfig()
        
        recs = gen._generate_recommendations(context, analysis, config)
        
        assert len(recs) > 0
        assert all(isinstance(r, ArchitecturalRecommendation) for r in recs)
    
    def test_identify_quick_wins(self):
        """Test quick wins identification."""
        gen = RoadmapGenerator()
        
        context = ProjectContext(
            project_name="test",
            repository_path="/path",
            primary_language="python",
        )
        
        recs = [
            ArchitecturalRecommendation(
                title="Add README",
                category=TechCategory.DOCUMENTATION,
                recommendation_type=Recommendation.IMPROVE,
                description="Test",
                why="Test",
                impact="Test",
                effort="low",
                priority=8,
            ),
            ArchitecturalRecommendation(
                title="Refactor large class",
                category=TechCategory.PATTERNS,
                recommendation_type=Recommendation.IMPROVE,
                description="Test",
                why="Test",
                impact="Test",
                effort="high",
                priority=7,
            ),
        ]
        
        quick_wins = gen._identify_quick_wins(context, recs)
        
        assert len(quick_wins) > 0
        assert "Add README" in quick_wins
    
    def test_create_vision(self):
        """Test vision creation."""
        gen = RoadmapGenerator()
        
        context = ProjectContext(
            project_name="my-project",
            repository_path="/path",
            primary_language="python",
        )
        
        vision = gen._create_vision(context)
        
        assert "my-project" in vision
        assert "python" in vision.lower()
    
    def test_create_90_day_plan(self):
        """Test 90 day plan creation."""
        gen = RoadmapGenerator()
        
        from src.roadmap.models import RoadmapPhaseInfo, PhaseItem
        
        phases = [
            RoadmapPhaseInfo(
                phase=RoadmapPhase.FOUNDATION,
                title="Foundation",
                description="Build foundation",
                estimated_duration_weeks=4,
                items=[
                    PhaseItem(title="Setup tests", description="Setup"),
                    PhaseItem(title="Add CI/CD", description="Setup"),
                ],
            )
        ]
        
        plan = gen._create_90_day_plan(phases)
        
        assert "Foundation" in plan or "setup" in plan.lower()
    
    def test_identify_risks(self):
        """Test risk identification."""
        gen = RoadmapGenerator()
        
        context = ProjectContext(
            project_name="test",
            repository_path="/path",
            primary_language="python",
            test_coverage=0.1,
            total_test_files=0,
            last_commit_age_days=200,
        )
        analysis = ProjectAnalysisResult(context=context)
        
        risks = gen._identify_risks(context, analysis)
        
        assert len(risks) > 0
        assert any("test" in k.lower() for k in risks.keys())


class TestArchitecturalRoadmap:
    """Test ArchitecturalRoadmap model."""
    
    def test_create_roadmap(self):
        """Create a complete roadmap."""
        context = ProjectContext(
            project_name="test",
            repository_path="/path",
            primary_language="python",
        )
        analysis = ProjectAnalysisResult(context=context)
        
        roadmap = ArchitecturalRoadmap(
            project_name="test",
            roadmap_id="test-id",
            context=context,
            analysis=analysis,
            recommendations=[],
            phases=[],
            best_practices=[],
        )
        
        assert roadmap.project_name == "test"
        assert roadmap.roadmap_id == "test-id"
    
    def test_critical_recommendations(self):
        """Test filtering critical recommendations."""
        context = ProjectContext(
            project_name="test",
            repository_path="/path",
            primary_language="python",
        )
        analysis = ProjectAnalysisResult(context=context)
        
        recs = [
            ArchitecturalRecommendation(
                title="Critical",
                category=TechCategory.TESTING,
                recommendation_type=Recommendation.IMPROVE,
                description="Test", why="Test", impact="Test",
                effort="low", priority=9, confidence_score=0.9,
            ),
            ArchitecturalRecommendation(
                title="Normal",
                category=TechCategory.DOCUMENTATION,
                recommendation_type=Recommendation.CONSIDER,
                description="Test", why="Test", impact="Test",
                effort="low", priority=5, confidence_score=0.8,
            ),
        ]
        
        roadmap = ArchitecturalRoadmap(
            project_name="test",
            roadmap_id="test-id",
            context=context,
            analysis=analysis,
            recommendations=recs,
            phases=[],
            best_practices=[],
        )
        
        critical = roadmap.critical_recommendations
        assert len(critical) == 1
        assert critical[0].priority == 9
    
    def test_overall_health_score(self):
        """Test overall health score calculation."""
        context = ProjectContext(
            project_name="test",
            repository_path="/path",
            primary_language="python",
        )
        analysis = ProjectAnalysisResult(
            context=context,
            architecture_score=7.0,
            test_score=6.0,
            documentation_score=5.0,
            security_score=8.0,
            maintainability_score=7.0,
            scalability_score=6.0,
        )
        
        roadmap = ArchitecturalRoadmap(
            project_name="test",
            roadmap_id="test-id",
            context=context,
            analysis=analysis,
        )
        
        score = roadmap.overall_health_score
        assert 5.0 <= score <= 8.0

