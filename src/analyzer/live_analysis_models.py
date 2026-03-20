"""Data models for live code analysis (UC-007)."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class QualityMetric(Enum):
    """Quality metrics to measure."""
    
    TYPE_HINTS = "type_hints"
    DOCSTRINGS = "docstrings"
    TEST_COVERAGE = "test_coverage"
    CODE_COMPLEXITY = "code_complexity"
    LOGGING = "logging"
    ERROR_HANDLING = "error_handling"
    COMMENTS = "comments"
    CONSISTENCY = "consistency"


class AnalysisStatus(Enum):
    """Status of code analysis."""
    
    ON_TRACK = "on_track"
    NEEDS_IMPROVEMENT = "needs_improvement"
    AT_RISK = "at_risk"
    EXCELLENT = "excellent"


class SuggestionPriority(Enum):
    """Priority of suggestions."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    OPTIONAL = "optional"


@dataclass
class CodeQualityMetrics:
    """Metrics for code quality assessment."""
    
    type_hints_ratio: float = 0.0  # 0.0-1.0
    docstring_ratio: float = 0.0
    test_coverage: float = 0.0
    cyclomatic_complexity: float = 10.0
    logging_presence: float = 0.0
    error_handling_ratio: float = 0.0
    comment_density: float = 0.0
    consistency_score: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "type_hints": self.type_hints_ratio,
            "docstrings": self.docstring_ratio,
            "test_coverage": self.test_coverage,
            "complexity": self.cyclomatic_complexity,
            "logging": self.logging_presence,
            "error_handling": self.error_handling_ratio,
            "comments": self.comment_density,
            "consistency": self.consistency_score,
        }


@dataclass
class PatternDeviation:
    """Represents a deviation from learned patterns."""
    
    pattern_type: str  # e.g., "missing_type_hints", "low_test_coverage"
    description: str
    severity: SuggestionPriority
    frequency_in_repos: float  # 0.0-1.0: how many repos follow this pattern
    your_score: float  # 0.0-1.0: your current score for this pattern
    target_score: float  # 0.0-1.0: recommended score
    improvement_needed: float  # target - your score
    example_code: Optional[str] = None
    related_patterns: List[str] = field(default_factory=list)


@dataclass
class QualityGate:
    """Quality gate validation."""
    
    name: str
    description: str
    threshold: float  # 0.0-1.0
    current_value: float
    passed: bool
    suggestion: str = ""


@dataclass
class StageValidation:
    """Validation against current roadmap stage."""
    
    current_stage: int = 1
    stage_name: str = ""
    expected_practices: List[str] = field(default_factory=list)
    missing_practices: List[str] = field(default_factory=list)
    aligned_practices: List[str] = field(default_factory=list)
    overall_alignment: float = 0.0  # 0.0-1.0


@dataclass
class CodeSuggestion:
    """A suggestion for code improvement."""
    
    title: str
    description: str
    priority: SuggestionPriority
    practice_adoption_rate: float  # % of repos following this
    action_required: str
    expected_benefit: str
    example_implementation: Optional[str] = None
    estimated_effort: str = "low"  # low/medium/high
    related_metric: Optional[QualityMetric] = None


@dataclass
class AnalyzedCode:
    """Result of code analysis."""
    
    project_id: str
    code_snippet: str
    language: str
    file_type: str
    metrics: CodeQualityMetrics
    deviations: List[PatternDeviation] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=datetime.now)


@dataclass
class LiveAnalysisResult:
    """Complete result of live code analysis."""
    
    project_id: str
    analysis_id: str
    status: AnalysisStatus
    overall_score: float  # 0.0-10.0
    
    # Analysis components
    current_stage: int
    code_metrics: CodeQualityMetrics
    deviations: List[PatternDeviation] = field(default_factory=list)
    suggestions: List[CodeSuggestion] = field(default_factory=list)
    quality_gates: List[QualityGate] = field(default_factory=list)
    stage_validation: Optional[StageValidation] = None
    
    # Comparison with patterns
    patterns_matched: int = 0
    patterns_total: int = 0
    
    # Recommendations
    next_milestone: str = ""
    urgent_fixes: List[str] = field(default_factory=list)
    improvements_available: List[str] = field(default_factory=list)
    
    # Metadata
    analyzed_at: datetime = field(default_factory=datetime.now)
    analysis_duration_ms: float = 0.0
    
    @property
    def pattern_alignment(self) -> float:
        """Alignment percentage with learned patterns."""
        if self.patterns_total == 0:
            return 0.0
        return (self.patterns_matched / self.patterns_total) * 100.0
    
    @property
    def critical_issues_count(self) -> int:
        """Count of critical issues."""
        return len([d for d in self.deviations 
                   if d.severity == SuggestionPriority.CRITICAL])
    
    @property
    def is_on_track(self) -> bool:
        """Whether project is on track for stage."""
        return self.status in [AnalysisStatus.ON_TRACK, AnalysisStatus.EXCELLENT]


@dataclass
class CodeAnalysisRequest:
    """Request for code analysis."""
    
    project_id: str
    code: str
    language: str = "python"
    file_path: str = ""
    current_stage: int = 1
    previous_score: Optional[float] = None
    include_deviations: bool = True
    include_suggestions: bool = True
    include_stage_validation: bool = True
    
    def validate(self):
        """Validate request."""
        if not self.project_id:
            raise ValueError("project_id required")
        if not self.code:
            raise ValueError("code required")
        if not (1 <= self.current_stage <= 6):
            raise ValueError("current_stage must be 1-6")


@dataclass
class AnalysisContext:
    """Context for analysis with learned patterns."""
    
    learned_patterns: Dict[str, float]  # pattern -> adoption_rate (0.0-1.0)
    stage_expectations: Dict[int, List[str]]  # stage -> expected practices
    best_practices: Dict[str, str]  # practice -> description
    language_config: Dict[str, Any] = field(default_factory=dict)
