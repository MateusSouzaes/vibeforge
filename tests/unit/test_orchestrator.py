"""Tests for processor orchestrator."""

import pytest
import tempfile
import json
from pathlib import Path
from src.processor.orchestrator import ProcessorOrchestrator


@pytest.fixture
def sample_project():
    """Create a complete sample project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create folder structure
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        
        # Python files
        (tmp_path / "src" / "main.py").write_text("def main():\n    pass")
        (tmp_path / "tests" / "test_main.py").write_text("def test():\n    pass")
        
        # Config files
        (tmp_path / "requirements.txt").write_text("pytest==8.0.0\n")
        (tmp_path / "README.md").write_text("# Project")
        (tmp_path / "Dockerfile").write_text("FROM python:3.12")
        
        yield tmp_path


@pytest.fixture
def sample_project_npm():
    """Create sample npm project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        package = {
            "name": "web-app",
            "dependencies": {
                "express": "^4.18.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package))
        (tmp_path / "index.js").write_text("console.log('app');")
        
        yield tmp_path


class TestProcessorOrchestrator:
    """Test suite for ProcessorOrchestrator."""

    def test_orchestrator_initialization(self, sample_project):
        """Test orchestrator initialization."""
        orchestrator = ProcessorOrchestrator(str(sample_project))
        
        assert orchestrator.repo_path == sample_project
        assert orchestrator.code_parser is not None
        assert orchestrator.stack_extractor is not None
        assert orchestrator.pattern_analyzer is not None

    def test_complete_analysis(self, sample_project):
        """Test complete analysis pipeline."""
        orchestrator = ProcessorOrchestrator(str(sample_project))
        parsed = orchestrator.analyze()
        
        assert parsed.repository_name == sample_project.name
        assert parsed.structure.total_files > 0
        assert len(parsed.files) > 0
        assert len(parsed.dependencies) > 0

    def test_analyze_and_export_json(self, sample_project):
        """Test analysis export to JSON."""
        orchestrator = ProcessorOrchestrator(str(sample_project))
        
        normalized = orchestrator.analyze_and_export_json()
        
        assert isinstance(normalized, dict)
        assert "structure" in normalized
        assert "files" in normalized
        assert "stack" in normalized

    def test_get_analysis_summary(self, sample_project):
        """Test getting analysis summary."""
        orchestrator = ProcessorOrchestrator(str(sample_project))
        summary = orchestrator.get_analysis_summary()
        
        assert summary["repository"] == sample_project.name
        assert "total_files" in summary
        assert "dependencies_count" in summary
        assert "patterns_detected" in summary
        assert summary["has_tests"] is True
        assert summary["has_docker"] is True

    def test_compare_projects(self, sample_project, sample_project_npm):
        """Test project comparison."""
        orchestrator1 = ProcessorOrchestrator(str(sample_project))
        comparison = orchestrator1.compare_projects(str(sample_project_npm))
        
        assert "project_1" in comparison
        assert "project_2" in comparison
        assert "similarities" in comparison
        assert "differences" in comparison

    def test_find_similarities(self, sample_project):
        """Test similarity detection."""
        orchestrator = ProcessorOrchestrator(str(sample_project))
        summary1 = orchestrator.get_analysis_summary()
        summary2 = {**summary1}  # Copy the summary
        
        similarities = orchestrator._find_similarities(summary1, summary2)
        
        # Identical projects should have many similarities
        assert isinstance(similarities, dict)

    def test_find_differences(self, sample_project):
        """Test difference detection."""
        orchestrator = ProcessorOrchestrator(str(sample_project))
        summary1 = orchestrator.get_analysis_summary()
        
        summary2 = {**summary1}
        summary2["total_files"] = 999  # Make them different
        
        differences = orchestrator._find_differences(summary1, summary2)
        
        assert "total_files" in differences

    def test_generate_report(self, sample_project):
        """Test report generation."""
        with tempfile.TemporaryDirectory() as output_dir:
            orchestrator = ProcessorOrchestrator(str(sample_project))
            results = orchestrator.generate_report(output_dir)
            
            assert "analysis" in results
            assert "summary" in results
            
            # Verify files were created
            assert Path(results["analysis"]).exists()
            assert Path(results["summary"]).exists()

    def test_export_json_to_file(self, sample_project):
        """Test exporting analysis to JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "analysis.json"
            
            orchestrator = ProcessorOrchestrator(str(sample_project))
            result = orchestrator.analyze_and_export_json(str(output_file))
            
            assert output_file.exists()
            
            # Verify file content
            with open(output_file) as f:
                data = json.load(f)
            
            assert data == result

    def test_dependencies_extracted(self, sample_project):
        """Test that dependencies are properly extracted."""
        orchestrator = ProcessorOrchestrator(str(sample_project))
        parsed = orchestrator.analyze()
        
        # Project has pytest in requirements.txt
        dep_names = [d.name for d in parsed.dependencies]
        assert "pytest" in dep_names

    def test_patterns_detected(self, sample_project):
        """Test that patterns are detected."""
        orchestrator = ProcessorOrchestrator(str(sample_project))
        parsed = orchestrator.analyze()
        
        # Should detect at least README documentation
        pattern_names = [p.name for p in parsed.detected_patterns]
        assert len(pattern_names) > 0

    def test_multiple_analysis_calls(self, sample_project):
        """Test running analysis multiple times."""
        orchestrator = ProcessorOrchestrator(str(sample_project))
        
        result1 = orchestrator.analyze()
        result2 = orchestrator.analyze()
        
        # Both should be successful and consistent
        assert result1.repository_name == result2.repository_name
        assert len(result1.files) == len(result2.files)
