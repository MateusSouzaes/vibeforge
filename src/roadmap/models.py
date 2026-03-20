"""Data models for roadmap generation."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from enum import Enum
from datetime import datetime


class RoadmapPhase(Enum):
    """Phases of development roadmap."""
    
    FOUNDATION = "foundation"  # Core architecture setup
    MVP = "mvp"  # Minimum Viable Product
    OPTIMIZATION = "optimization"  # Performance improvements
    SCALING = "scaling"  # Scalability features
    MATURITY = "maturity"  # Production-grade


class TechCategory(Enum):
    """Technology categories for recommendations."""
    
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MONITORING = "monitoring"
    PATTERNS = "patterns"


class Recommendation(Enum):
    """Types of recommendations."""
    
    ADOPT = "adopt"  # Strongly recommended
    CONSIDER = "consider"  # Worth evaluating
    AVOID = "avoid"  # Anti-pattern detected
    IMPROVE = "improve"  # Current implementation needs improvement
    MAINTAIN = "maintain"  # Already good


@dataclass
class ProjectContext:
    """Context information about the project being analyzed."""
    
    project_name: str
    repository_path: str
    primary_language: str
    detected_frameworks: List[str] = field(default_factory=list)
    total_code_files: int = 0
    total_test_files: int = 0
    test_coverage: float = 0.0
    code_complexity: float = 0.0  # Average cyclomatic complexity
    technical_debt: float = 0.0  # 0.0-1.0 score
    project_age_days: int = 0
    contributors_count: int = 0
    last_commit_age_days: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchitecturalRecommendation:
    """Recommendation for architecture improvement."""
    
    title: str
    category: TechCategory
    recommendation_type: Recommendation
    description: str
    why: str  # Why this matters
    impact: str  # Potential impact
    effort: str  # Implementation effort (low/medium/high)
    priority: int  # 1-10, 10 being highest
    related_patterns: List[str] = field(default_factory=list)
    example_reference: Optional[str] = None
    confidence_score: float = 0.8  # 0.0-1.0
    
    def __post_init__(self):
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("confidence_score must be 0.0-1.0")
        if not (1 <= self.priority <= 10):
            raise ValueError("priority must be 1-10")


@dataclass
class PhaseItem:
    """Item in a roadmap phase."""
    
    title: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    estimated_duration_weeks: int = 1
    success_criteria: List[str] = field(default_factory=list)
    related_recommendations: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)


@dataclass
class RoadmapPhaseInfo:
    """Information about a roadmap phase."""
    
    phase: RoadmapPhase
    title: str
    description: str
    estimated_duration_weeks: int
    items: List[PhaseItem] = field(default_factory=list)
    prerequisites: List[RoadmapPhase] = field(default_factory=list)
    expected_outcomes: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)


@dataclass
class BestPractice:
    """Best practice suggestion."""
    
    title: str
    category: TechCategory
    description: str
    benefits: List[str] = field(default_factory=list)
    implementation_steps: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)  # URLs or references
    is_currently_applied: bool = False
    confidence_score: float = 0.8


@dataclass
class ProjectAnalysisResult:
    """Result of project analysis."""
    
    context: ProjectContext
    detected_patterns: List[str] = field(default_factory=list)
    identified_issues: List[str] = field(default_factory=list)
    architecture_score: float = 0.0  # 0.0-10.0
    test_score: float = 0.0
    documentation_score: float = 0.0
    security_score: float = 0.0
    maintainability_score: float = 0.0
    scalability_score: float = 0.0
    analyzed_at: datetime = field(default_factory=datetime.now)


@dataclass
class ArchitecturalRoadmap:
    """Complete architectural roadmap for a project."""
    
    project_name: str
    roadmap_id: str
    context: ProjectContext
    analysis: ProjectAnalysisResult
    recommendations: List[ArchitecturalRecommendation] = field(default_factory=list)
    phases: List[RoadmapPhaseInfo] = field(default_factory=list)
    best_practices: List[BestPractice] = field(default_factory=list)
    quick_wins: List[str] = field(default_factory=list)  # Quick improvements
    long_term_vision: str = ""
    next_90_days: str = ""
    risks_and_mitigation: Dict[str, str] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def critical_recommendations(self) -> List[ArchitecturalRecommendation]:
        """Get high-priority recommendations."""
        return [r for r in self.recommendations if r.priority >= 8]
    
    @property
    def overall_health_score(self) -> float:
        """Calculate project overall health score."""
        scores = [
            self.analysis.architecture_score,
            self.analysis.test_score,
            self.analysis.documentation_score,
            self.analysis.security_score,
            self.analysis.maintainability_score,
            self.analysis.scalability_score,
        ]
        return sum(scores) / len(scores) if scores else 0.0


@dataclass
class RoadmapConfig:
    """Configuration for roadmap generation."""
    
    include_patterns: bool = True
    include_best_practices: bool = True
    include_quick_wins: bool = True
    focus_areas: List[TechCategory] = field(default_factory=lambda: [cat for cat in TechCategory])
    max_recommendations: int = 20
    min_confidence_threshold: float = 0.6
    phases_to_generate: int = 4  # Number of phases in roadmap
    include_risk_analysis: bool = True
    include_metrics: bool = True
    
    def validate(self):
        """Validate configuration."""
        if self.max_recommendations < 1:
            raise ValueError("max_recommendations must be >= 1")
        if not (0.0 <= self.min_confidence_threshold <= 1.0):
            raise ValueError("min_confidence_threshold must be 0.0-1.0")
        if self.phases_to_generate < 1:
            raise ValueError("phases_to_generate must be >= 1")
