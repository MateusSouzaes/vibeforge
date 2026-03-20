"""Tests for pattern analyzer module."""

import pytest
import tempfile
from pathlib import Path
from src.processor.pattern_analyzer import PatternAnalyzer


@pytest.fixture
def mvc_project():
    """Create project with MVC pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        (tmp_path / "models").mkdir()
        (tmp_path / "views").mkdir()
        (tmp_path / "controllers").mkdir()
        
        (tmp_path / "models" / "user.py").write_text("class User: pass")
        (tmp_path / "views" / "home.html").write_text("<html></html>")
        (tmp_path / "controllers" / "user_controller.py").write_text("class UserController: pass")
        
        yield tmp_path


@pytest.fixture
def testing_project():
    """Create project with testing patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_user.py").write_text("""
def test_create_user():
    assert True

def test_delete_user():
    pass
""")
        
        yield tmp_path


@pytest.fixture
def documented_project():
    """Create well-documented project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        (tmp_path / "README.md").write_text("# My Project")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "api.md").write_text("# API Documentation")
        
        (tmp_path / "app.py").write_text('''
def calculate(a: int, b: int) -> int:
    """Calculate sum of two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    """
    return a + b
''')
        
        yield tmp_path


@pytest.fixture
def design_pattern_project():
    """Create project with design patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        (tmp_path / "factory.py").write_text("""
class UserFactory:
    def create_user(self, name):
        return User(name)
""")
        
        (tmp_path / "singleton.py").write_text("""
class Logger:
    _instance = None
    
    @staticmethod
    def getInstance():
        if Logger._instance is None:
            Logger._instance = Logger()
        return Logger._instance
""")
        
        yield tmp_path


class TestPatternAnalyzer:
    """Test suite for PatternAnalyzer."""

    def test_analyzer_initialization(self, mvc_project):
        """Test analyzer can be initialized."""
        analyzer = PatternAnalyzer(str(mvc_project))
        assert analyzer.repo_path == mvc_project

    def test_detect_mvc_pattern(self, mvc_project):
        """Test MVC pattern detection."""
        analyzer = PatternAnalyzer(str(mvc_project))
        patterns = analyzer._detect_architectural_patterns()
        
        pattern_names = [p.name for p in patterns]
        assert "MVC Architecture" in pattern_names

    def test_detect_testing_patterns(self, testing_project):
        """Test testing pattern detection."""
        analyzer = PatternAnalyzer(str(testing_project))
        patterns = analyzer._detect_testing_patterns()
        
        pattern_names = [p.name for p in patterns]
        assert "Unit Testing" in pattern_names

    def test_detect_documentation_patterns(self, documented_project):
        """Test documentation pattern detection."""
        analyzer = PatternAnalyzer(str(documented_project))
        patterns = analyzer._detect_documentation_patterns()
        
        pattern_names = [p.name for p in patterns]
        assert "README Documentation" in pattern_names
        assert "API Documentation" in pattern_names

    def test_detect_type_hints(self, documented_project):
        """Test type hints detection."""
        analyzer = PatternAnalyzer(str(documented_project))
        
        # Verify the method runs without error
        patterns = analyzer._detect_code_style_patterns()
        assert isinstance(patterns, list)

    def test_detect_design_patterns(self, design_pattern_project):
        """Test design pattern detection."""
        analyzer = PatternAnalyzer(str(design_pattern_project))
        patterns = analyzer._detect_design_patterns()
        
        pattern_names = [p.name for p in patterns]
        assert "Factory Pattern" in pattern_names
        assert "Singleton Pattern" in pattern_names

    def test_analyze_all_patterns(self, documented_project):
        """Test comprehensive pattern analysis."""
        analyzer = PatternAnalyzer(str(documented_project))
        patterns = analyzer.analyze_patterns()
        
        assert len(patterns) > 0
        assert all(p.name for p in patterns)

    def test_pattern_summary(self, documented_project):
        """Test pattern summary generation."""
        analyzer = PatternAnalyzer(str(documented_project))
        patterns = analyzer.analyze_patterns()
        summary = analyzer.get_pattern_summary(patterns)
        
        assert isinstance(summary, dict)
        assert len(summary) > 0
        assert all(isinstance(v, int) for v in summary.values())

    def test_contains_pattern_method(self, documented_project):
        """Test pattern matching utility."""
        analyzer = PatternAnalyzer(str(documented_project))
        app_file = documented_project / "app.py"
        
        # Should find type hints
        assert analyzer._contains_pattern(app_file, r"->\s*\w+")
        
        # Should find function definition
        assert analyzer._contains_pattern(app_file, r"def\s+\w+")

    def test_empty_project(self):
        """Test analyzer on empty project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = PatternAnalyzer(str(tmpdir))
            patterns = analyzer.analyze_patterns()
            
            # Empty project should have minimal patterns
            assert isinstance(patterns, list)

    def test_pattern_frequency(self, design_pattern_project):
        """Test pattern frequency counting."""
        analyzer = PatternAnalyzer(str(design_pattern_project))
        patterns = analyzer._detect_design_patterns()
        
        # Patterns should have frequency > 0
        assert all(p.frequency > 0 for p in patterns)
