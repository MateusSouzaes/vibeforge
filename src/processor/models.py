"""Data models for code parsing and pattern extraction (using dataclasses)."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class LanguageType(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    CSHARP = "csharp"


@dataclass
class Dependency:
    """Represents a single dependency/package."""
    name: str
    version: Optional[str] = None
    source: str = field(default="unknown")  # pip, npm, cargo, etc


@dataclass
class CodePattern:
    """Represents a detected code pattern."""
    name: str
    description: Optional[str] = None
    frequency: int = field(default=1)
    examples: List[str] = field(default_factory=list)


@dataclass
class FileMetadata:
    """Metadata about a single file."""
    path: str
    language: LanguageType
    lines_of_code: int
    has_tests: bool = False
    complexity: Optional[str] = None


@dataclass
class ProjectStructure:
    """Information about project folder structure."""
    total_files: int
    languages: Dict[str, int] = field(default_factory=dict)
    main_folders: List[str] = field(default_factory=list)


@dataclass
class ParsedProject:
    """Complete parsed project information."""
    repository_name: str
    primary_language: LanguageType
    structure: ProjectStructure
    dependencies: List[Dependency] = field(default_factory=list)
    detected_patterns: List[CodePattern] = field(default_factory=list)
    files: List[FileMetadata] = field(default_factory=list)
    has_ci_cd: bool = False
    has_dockerfile: bool = False
    has_makefile: bool = False
    config_files: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
