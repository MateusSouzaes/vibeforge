"""Data models for git history analysis."""

from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import List, Optional


class ChangeType(Enum):
    """Types of code changes in commits."""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    TEST = "test"
    DOCS = "docs"
    CONFIG = "config"
    CHORE = "chore"
    BREAKING = "breaking"


class DecisionType(Enum):
    """Types of architectural/technical decisions."""
    ARCHITECTURE = "architecture"
    DEPENDENCY = "dependency"
    PATTERN = "pattern"
    CONSTRAINT = "constraint"
    REMOVAL = "removal"
    MIGRATION = "migration"


@dataclass
class CommitAuthor:
    """Information about a commit author."""
    name: str
    email: str
    commits_count: int = 0
    first_commit_date: Optional[datetime] = None
    last_commit_date: Optional[datetime] = None


@dataclass
class ChangePattern:
    """Pattern of changes in a commit."""
    file_count: int
    added_lines: int
    removed_lines: int
    modified_lines: int
    file_extensions: List[str]
    change_type: ChangeType


@dataclass
class Decision:
    """Architectural/technical decision extracted from commits."""
    name: str
    description: str
    decision_type: DecisionType
    commit_hash: str
    commit_date: datetime
    rationale: Optional[str] = None
    impact_areas: List[str] = None
    
    def __post_init__(self):
        if self.impact_areas is None:
            self.impact_areas = []


@dataclass
class EvolutionPhase:
    """Phase in project evolution based on commit patterns."""
    name: str
    start_date: datetime
    end_date: datetime
    duration_days: int
    commit_count: int
    primary_focus: str
    key_decisions: List[str]
    contributors: List[str]


@dataclass
class AnalyzedCommit:
    """Complete analysis of a single commit."""
    hash: str
    message: str
    author: CommitAuthor
    date: datetime
    change_pattern: ChangePattern
    detected_decisions: List[Decision]
    related_commits: List[str]
    significance_score: float  # 0.0-1.0


@dataclass
class CommitHistoryAnalysis:
    """Complete history analysis of a repository."""
    repository_name: str
    total_commits: int
    date_range_start: datetime
    date_range_end: datetime
    duration_days: int
    contributors: List[CommitAuthor]
    analyzed_commits: List[AnalyzedCommit]
    decisions: List[Decision]
    evolution_phases: List[EvolutionPhase]
    commit_patterns: dict  # Summary of patterns
