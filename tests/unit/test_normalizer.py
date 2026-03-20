"""Tests for normalizer module."""

import pytest
import json
import tempfile
from pathlib import Path
from src.processor.models import (
    LanguageType,
    ParsedProject,
    ProjectStructure,
    Dependency,
    CodePattern,
    FileMetadata,
)
from src.processor.normalizer import Normalizer


@pytest.fixture
def sample_project():
    """Create a sample ParsedProject for testing."""
    structure = ProjectStructure(
        total_files=42,
        languages={"python": 35, "javascript": 7},
        main_folders=["src", "tests", "docs"],
    )
    
    dependencies = [
        Dependency(name="pytest", version="8.0.0", source="pip"),
        Dependency(name="requests", version="2.31.0", source="pip"),
        Dependency(name="react", version="18.0.0", source="npm"),
    ]
    
    patterns = [
        CodePattern(
            name="Unit Testing",
            description="Testing framework detected",
            frequency=1,
            examples=["tests/"],
        ),
        CodePattern(
            name="MVC Architecture",
            description="MVC pattern detected",
            frequency=1,
        ),
    ]
    
    files = [
        FileMetadata(
            path="src/main.py",
            language=LanguageType.PYTHON,
            lines_of_code=150,
            has_tests=False,
        ),
        FileMetadata(
            path="tests/test_main.py",
            language=LanguageType.PYTHON,
            lines_of_code=80,
            has_tests=True,
        ),
    ]
    
    return ParsedProject(
        repository_name="test-project",
        primary_language=LanguageType.PYTHON,
        structure=structure,
        dependencies=dependencies,
        detected_patterns=patterns,
        files=files,
        has_dockerfile=True,
        has_ci_cd=True,
        has_makefile=False,
        config_files=["pyproject.toml", "pytest.ini"],
    )


class TestNormalizer:
    """Test suite for Normalizer."""

    def test_to_dict_structure(self, sample_project):
        """Test conversion to dictionary."""
        result = Normalizer.to_dict(sample_project)
        
        assert "repository" in result
        assert "structure" in result
        assert "stack" in result
        assert "patterns" in result
        assert "files" in result
        assert "infrastructure" in result

    def test_to_dict_repository_section(self, sample_project):
        """Test repository section of dict."""
        result = Normalizer.to_dict(sample_project)
        
        assert result["repository"]["name"] == "test-project"
        assert result["repository"]["primary_language"] == "python"

    def test_to_dict_structure_section(self, sample_project):
        """Test structure section of dict."""
        result = Normalizer.to_dict(sample_project)
        
        assert result["structure"]["total_files"] == 42
        assert result["structure"]["languages"] == {"python": 35, "javascript": 7}
        assert "src" in result["structure"]["main_folders"]

    def test_to_dict_stack_section(self, sample_project):
        """Test stack section of dict."""
        result = Normalizer.to_dict(sample_project)
        
        assert result["stack"]["total_dependencies"] == 3
        assert len(result["stack"]["dependencies"]) == 3
        assert result["stack"]["dependencies"][0]["name"] == "pytest"

    def test_to_dict_patterns_section(self, sample_project):
        """Test patterns section of dict."""
        result = Normalizer.to_dict(sample_project)
        
        assert result["patterns"]["total_patterns"] == 2
        assert len(result["patterns"]["detected"]) == 2
        assert result["patterns"]["detected"][0]["name"] == "Unit Testing"

    def test_to_dict_infrastructure_section(self, sample_project):
        """Test infrastructure section of dict."""
        result = Normalizer.to_dict(sample_project)
        
        assert result["infrastructure"]["has_dockerfile"] is True
        assert result["infrastructure"]["has_ci_cd"] is True
        assert result["infrastructure"]["has_makefile"] is False
        assert "pyproject.toml" in result["infrastructure"]["config_files"]

    def test_to_json_format(self, sample_project):
        """Test JSON string generation."""
        json_str = Normalizer.to_json(sample_project)
        
        # Should be valid JSON
        data = json.loads(json_str)
        assert isinstance(data, dict)
        assert "repository" in data

    def test_to_json_formatting(self, sample_project):
        """Test JSON formatting with indentation."""
        json_str = Normalizer.to_json(sample_project, indent=2)
        
        # Should have newlines (formatted)
        assert "\n" in json_str
        
        # Should be valid JSON
        data = json.loads(json_str)
        assert data is not None

    def test_to_file(self, sample_project):
        """Test writing to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "output.json"
            Normalizer.to_file(sample_project, str(filepath))
            
            assert filepath.exists()
            
            # Load and verify
            data = json.loads(filepath.read_text())
            assert data["repository"]["name"] == "test-project"

    def test_to_file_creates_directories(self, sample_project):
        """Test that to_file creates necessary directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "nested" / "output.json"
            Normalizer.to_file(sample_project, str(filepath))
            
            assert filepath.exists()

    def test_validate_structure_valid(self, sample_project):
        """Test validation of valid structure."""
        data = Normalizer.to_dict(sample_project)
        assert Normalizer.validate_structure(data) is True

    def test_validate_structure_invalid(self):
        """Test validation of invalid structure."""
        invalid_data = {"repository": {}}
        assert Normalizer.validate_structure(invalid_data) is False

    def test_get_summary(self, sample_project):
        """Test summary generation."""
        data = Normalizer.to_dict(sample_project)
        summary = Normalizer.get_summary(data)
        
        assert summary["project_name"] == "test-project"
        assert summary["primary_language"] == "python"
        assert summary["total_files"] == 42
        assert summary["total_dependencies"] == 3
        assert summary["total_patterns"] == 2

    def test_compare_projects(self, sample_project):
        """Test project comparison."""
        data1 = Normalizer.to_dict(sample_project)
        
        # Create a second similar project
        structure2 = ProjectStructure(
            total_files=50,
            languages={"python": 40, "javascript": 10},
            main_folders=["src", "tests"],
        )
        project2 = ParsedProject(
            repository_name="test-project-2",
            primary_language=LanguageType.PYTHON,
            structure=structure2,
            has_dockerfile=True,
            has_ci_cd=True,
        )
        data2 = Normalizer.to_dict(project2)
        
        comparison = Normalizer.compare_projects(data1, data2)
        
        assert "similarities" in comparison
        assert "differences" in comparison
        assert comparison["similarities"]["same_primary_language"] is True
        assert comparison["differences"]["file_count_diff"] == -8
