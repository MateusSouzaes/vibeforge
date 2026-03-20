"""Normalize and standardize project analysis output to JSON."""

import json
from pathlib import Path
from typing import Dict, Any
from dataclasses import asdict
from src.processor.models import ParsedProject


class Normalizer:
    """Convert ParsedProject to standardized JSON format."""

    @staticmethod
    def to_dict(project: ParsedProject) -> Dict[str, Any]:
        """Convert ParsedProject to dictionary.
        
        Args:
            project: ParsedProject instance
            
        Returns:
            Dictionary representation
        """
        return {
            "repository": {
                "name": project.repository_name,
                "primary_language": project.primary_language.value,
            },
            "structure": {
                "total_files": project.structure.total_files,
                "languages": project.structure.languages,
                "main_folders": project.structure.main_folders,
            },
            "stack": {
                "dependencies": [
                    {
                        "name": dep.name,
                        "version": dep.version,
                        "source": dep.source,
                    }
                    for dep in project.dependencies
                ],
                "total_dependencies": len(project.dependencies),
            },
            "patterns": {
                "detected": [
                    {
                        "name": pattern.name,
                        "description": pattern.description,
                        "frequency": pattern.frequency,
                        "examples": pattern.examples,
                    }
                    for pattern in project.detected_patterns
                ],
                "total_patterns": len(project.detected_patterns),
            },
            "files": {
                "count": len(project.files),
                "by_language": {
                    file.language.value: sum(
                        1 for f in project.files
                        if f.language == file.language
                    )
                    for file in project.files
                },
                "with_tests": sum(1 for f in project.files if f.has_tests),
            },
            "infrastructure": {
                "has_dockerfile": project.has_dockerfile,
                "has_makefile": project.has_makefile,
                "has_ci_cd": project.has_ci_cd,
                "config_files": project.config_files,
            },
            "metadata": project.metadata,
        }

    @staticmethod
    def to_json(project: ParsedProject, indent: int = 2) -> str:
        """Convert ParsedProject to formatted JSON string.
        
        Args:
            project: ParsedProject instance
            indent: JSON indentation level
            
        Returns:
            JSON string
        """
        data = Normalizer.to_dict(project)
        return json.dumps(data, indent=indent, ensure_ascii=False)

    @staticmethod
    def to_file(project: ParsedProject, filepath: str) -> None:
        """Write ParsedProject to JSON file.
        
        Args:
            project: ParsedProject instance
            filepath: Path to output file
        """
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        json_str = Normalizer.to_json(project)
        output_path.write_text(json_str, encoding="utf-8")

    @staticmethod
    def validate_structure(data: Dict[str, Any]) -> bool:
        """Validate JSON structure.
        
        Args:
            data: Dictionary to validate
            
        Returns:
            True if structure is valid
        """
        required_keys = {
            "repository",
            "structure",
            "stack",
            "patterns",
            "files",
            "infrastructure",
        }
        
        return all(key in data for key in required_keys)

    @staticmethod
    def get_summary(data: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary statistics from normalized data.
        
        Args:
            data: Normalized project data
            
        Returns:
            Summary dictionary
        """
        return {
            "project_name": data["repository"]["name"],
            "primary_language": data["repository"]["primary_language"],
            "total_files": data["structure"]["total_files"],
            "total_dependencies": data["stack"]["total_dependencies"],
            "total_patterns": data["patterns"]["total_patterns"],
            "languages_used": len(data["structure"]["languages"]),
            "has_ci_cd": data["infrastructure"]["has_ci_cd"],
            "has_dockerfile": data["infrastructure"]["has_dockerfile"],
        }

    @staticmethod
    def compare_projects(project1: Dict[str, Any], project2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two normalized projects.
        
        Args:
            project1: First project data
            project2: Second project data
            
        Returns:
            Comparison data
        """
        return {
            "similarities": {
                "same_primary_language": (
                    project1["repository"]["primary_language"] ==
                    project2["repository"]["primary_language"]
                ),
                "both_have_docker": (
                    project1["infrastructure"]["has_dockerfile"] ==
                    project2["infrastructure"]["has_dockerfile"]
                ),
                "both_have_ci_cd": (
                    project1["infrastructure"]["has_ci_cd"] ==
                    project2["infrastructure"]["has_ci_cd"]
                ),
            },
            "differences": {
                "file_count_diff": (
                    project1["structure"]["total_files"] -
                    project2["structure"]["total_files"]
                ),
                "dependency_count_diff": (
                    project1["stack"]["total_dependencies"] -
                    project2["stack"]["total_dependencies"]
                ),
                "pattern_count_diff": (
                    project1["patterns"]["total_patterns"] -
                    project2["patterns"]["total_patterns"]
                ),
            },
        }
