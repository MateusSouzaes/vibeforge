"""Tests for code parser module."""

import pytest
import tempfile
from pathlib import Path
from src.processor.code_parser import CodeParser
from src.processor.models import LanguageType


@pytest.fixture
def temp_python_project():
    """Create a temporary Python project structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create Python files
        (tmp_path / "main.py").write_text("def hello():\n    pass\n")
        (tmp_path / "utils.py").write_text("# Utility functions\n" * 10)
        (tmp_path / "test_main.py").write_text("import pytest\n")
        
        # Create folder structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "handlers.py").write_text("class Handler:\n    pass\n")
        
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_utils.py").write_text("# test\n")
        
        # Config files
        (tmp_path / "requirements.txt").write_text("pytest==8.0.0\n")
        
        yield tmp_path


@pytest.fixture
def temp_mixed_project():
    """Create a temporary mixed language project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Python files
        (tmp_path / "app.py").write_text("# Python app\n" * 20)
        
        # JavaScript files
        (tmp_path / "index.js").write_text("console.log('hello');\n" * 15)
        (tmp_path / "utils.js").write_text("// utils\n")
        
        # Rust file
        (tmp_path / "lib.rs").write_text("fn main() {}\n")
        
        # Config
        (tmp_path / "Dockerfile").write_text("FROM python:3.12\n")
        
        yield tmp_path


class TestCodeParser:
    """Test suite for CodeParser."""

    def test_parser_initialization(self, temp_python_project):
        """Test parser can be initialized with valid path."""
        parser = CodeParser(str(temp_python_project))
        assert parser.repo_path == temp_python_project
        assert parser.repo_name == temp_python_project.name

    def test_parser_invalid_path(self):
        """Test parser raises error for invalid path."""
        with pytest.raises(ValueError, match="does not exist"):
            parser = CodeParser("/nonexistent/path")
            parser.parse()

    def test_scan_files_python_project(self, temp_python_project):
        """Test file scanning finds all code files."""
        parser = CodeParser(str(temp_python_project))
        files = parser._scan_files()
        
        assert len(files) >= 4  # main.py, utils.py, test_main.py, handlers.py, test_utils.py
        assert any(f.path.endswith("main.py") for f in files)
        assert all(f.language == LanguageType.PYTHON for f in files)

    def test_detect_test_files(self, temp_python_project):
        """Test parser correctly identifies test files."""
        parser = CodeParser(str(temp_python_project))
        files = parser._scan_files()
        
        test_files = [f for f in files if f.has_tests]
        non_test_files = [f for f in files if not f.has_tests]
        
        assert len(test_files) >= 2
        assert len(non_test_files) >= 2
        assert all("test" in f.path for f in test_files)

    def test_determine_primary_language_python(self, temp_python_project):
        """Test primary language detection for Python project."""
        parser = CodeParser(str(temp_python_project))
        files = parser._scan_files()
        primary = parser._determine_primary_language(files)
        
        assert primary == LanguageType.PYTHON

    def test_analyze_structure(self, temp_python_project):
        """Test project structure analysis."""
        parser = CodeParser(str(temp_python_project))
        files = parser._scan_files()
        structure = parser._analyze_structure(files)
        
        assert structure.total_files == len(files)
        assert "python" in structure.languages
        assert structure.languages["python"] >= 3  # At least some Python files

    def test_count_lines(self, temp_python_project):
        """Test line counting."""
        parser = CodeParser(str(temp_python_project))
        
        test_file = temp_python_project / "utils.py"
        lines = parser._count_lines(test_file)
        
        assert lines > 0
        assert lines >= 10  # We wrote 10 comment lines

    def test_has_config_files(self, temp_python_project):
        """Test config file detection."""
        parser = CodeParser(str(temp_python_project))
        
        assert parser._has_makefile() is False
        assert (temp_python_project / "requirements.txt").exists()

    def test_mixed_language_project(self, temp_mixed_project):
        """Test parsing project with multiple languages."""
        parser = CodeParser(str(temp_mixed_project))
        files = parser._scan_files()
        
        languages = {f.language for f in files}
        assert LanguageType.PYTHON in languages
        assert LanguageType.JAVASCRIPT in languages
        assert LanguageType.RUST in languages

    def test_has_dockerfile_detection(self, temp_mixed_project):
        """Test Dockerfile detection."""
        parser = CodeParser(str(temp_mixed_project))
        
        assert parser._has_dockerfile() is True

    def test_parse_full_project(self, temp_python_project):
        """Test full project parsing."""
        parser = CodeParser(str(temp_python_project))
        result = parser.parse()
        
        assert result.repository_name == temp_python_project.name
        assert result.primary_language == LanguageType.PYTHON
        assert result.structure.total_files > 0
        assert len(result.files) > 0
        assert result.structure.total_files == len(result.files)
