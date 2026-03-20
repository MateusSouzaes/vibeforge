"""Orchestrator that integrates all processor modules."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from src.processor.code_parser import CodeParser
from src.processor.stack_extractor import StackExtractor
from src.processor.pattern_analyzer import PatternAnalyzer
from src.processor.normalizer import Normalizer
from src.processor.models import ParsedProject


class ProcessorOrchestrator:
    """Orchestrates the complete code analysis pipeline."""

    def __init__(self, repo_path: str):
        """Initialize orchestrator.
        
        Args:
            repo_path: Path to repository to analyze
        """
        self.repo_path = Path(repo_path)
        
        self.code_parser = CodeParser(str(repo_path))
        self.stack_extractor = StackExtractor(str(repo_path))
        self.pattern_analyzer = PatternAnalyzer(str(repo_path))

    def analyze(self) -> ParsedProject:
        """Run complete analysis pipeline.
        
        Returns:
            Comprehensive ParsedProject with all analysis
        """
        # Step 1: Parse code structure
        parsed = self.code_parser.parse()
        
        # Step 2: Extract dependencies
        parsed.dependencies = self.stack_extractor.extract_all_dependencies()
        
        # Step 3: Detect patterns
        parsed.detected_patterns = self.pattern_analyzer.analyze_patterns()
        
        return parsed

    def analyze_and_export_json(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Run analysis and export to JSON.
        
        Args:
            output_path: Optional path to save JSON file
            
        Returns:
            Dictionary representation of analysis
        """
        parsed = self.analyze()
        
        # Normalize to dictionary
        normalized = Normalizer.to_dict(parsed)
        
        # Save to file if path provided
        if output_path:
            Normalizer.to_file(parsed, output_path)
        
        return normalized

    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get high-level summary of analysis.
        
        Returns:
            Summary dictionary
        """
        parsed = self.analyze()
        
        return {
            "repository": parsed.repository_name,
            "primary_language": parsed.primary_language.value,
            "total_files": parsed.structure.total_files,
            "languages_supported": parsed.structure.languages,
            "dependencies_count": len(parsed.dependencies),
            "patterns_detected": len(parsed.detected_patterns),
            "main_folders": parsed.structure.main_folders,
            "config_files": parsed.config_files,
            "has_tests": any(f.has_tests for f in parsed.files),
            "has_ci_cd": parsed.has_ci_cd,
            "has_docker": parsed.has_dockerfile,
        }

    def compare_projects(self, other_repo_path: str) -> Dict[str, Any]:
        """Compare this project with another.
        
        Args:
            other_repo_path: Path to other repository
            
        Returns:
            Comparison dictionary
        """
        other_orchestrator = ProcessorOrchestrator(other_repo_path)
        
        this_summary = self.get_analysis_summary()
        other_summary = other_orchestrator.get_analysis_summary()
        
        return {
            "project_1": this_summary,
            "project_2": other_summary,
            "similarities": self._find_similarities(this_summary, other_summary),
            "differences": self._find_differences(this_summary, other_summary),
        }

    def _find_similarities(self, summary1: Dict, summary2: Dict) -> Dict[str, Any]:
        """Find similarities between two project summaries.
        
        Args:
            summary1: First project summary
            summary2: Second project summary
            
        Returns:
            Similarities dictionary
        """
        similarities = {}
        
        # Compare languages
        if summary1.get("languages_supported") == summary2.get("languages_supported"):
            similarities["same_languages"] = True
        
        # Compare if both have tests
        if summary1.get("has_tests") == summary2.get("has_tests"):
            similarities["same_testing_setup"] = summary1.get("has_tests")
        
        # Compare CI/CD
        if summary1.get("has_ci_cd") == summary2.get("has_ci_cd"):
            similarities["same_ci_cd"] = summary1.get("has_ci_cd")
        
        return similarities

    def _find_differences(self, summary1: Dict, summary2: Dict) -> Dict[str, Any]:
        """Find differences between two project summaries.
        
        Args:
            summary1: First project summary
            summary2: Second project summary
            
        Returns:
            Differences dictionary
        """
        differences = {}
        
        if summary1.get("primary_language") != summary2.get("primary_language"):
            differences["primary_language"] = {
                "project_1": summary1.get("primary_language"),
                "project_2": summary2.get("primary_language"),
            }
        
        if summary1.get("total_files") != summary2.get("total_files"):
            differences["total_files"] = {
                "project_1": summary1.get("total_files"),
                "project_2": summary2.get("total_files"),
            }
        
        if summary1.get("dependencies_count") != summary2.get("dependencies_count"):
            differences["dependencies"] = {
                "project_1": summary1.get("dependencies_count"),
                "project_2": summary2.get("dependencies_count"),
            }
        
        return differences

    def generate_report(self, output_dir: Optional[str] = None) -> Dict[str, str]:
        """Generate complete analysis report.
        
        Args:
            output_dir: Optional directory to save report files
            
        Returns:
            Dictionary with file paths created
        """
        results = {}
        
        # Run analysis
        parsed = self.analyze()
        normalized = Normalizer.to_dict(parsed)
        
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save main analysis
            analysis_file = output_path / f"{parsed.repository_name}_analysis.json"
            with open(analysis_file, "w") as f:
                json.dump(normalized, f, indent=2)
            results["analysis"] = str(analysis_file)
            
            # Save summary
            summary = self.get_analysis_summary()
            summary_file = output_path / f"{parsed.repository_name}_summary.json"
            with open(summary_file, "w") as f:
                json.dump(summary, f, indent=2)
            results["summary"] = str(summary_file)
        
        return results
