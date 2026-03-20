"""Quality checker - Validates code against quality standards."""

import logging
from typing import List, Dict, Tuple

from src.analyzer.live_analysis_models import (
    CodeQualityMetrics, QualityGate, SuggestionPriority
)


logger = logging.getLogger(__name__)


class QualityChecker:
    """Checks code quality against standards."""
    
    # Quality thresholds by severity
    THRESHOLDS = {
        "type_hints": {"critical": 0.9, "high": 0.7, "medium": 0.5},
        "docstrings": {"critical": 0.8, "high": 0.6, "medium": 0.4},
        "test_coverage": {"critical": 0.8, "high": 0.6, "medium": 0.3},
        "complexity": {"critical": 5.0, "high": 10.0, "medium": 15.0},
        "error_handling": {"critical": 0.8, "high": 0.5, "medium": 0.3},
        "logging": {"critical": 0.9, "high": 0.6, "medium": 0.3},
    }
    
    def __init__(self):
        """Initialize quality checker."""
        self.logger = logging.getLogger(__name__)
    
    def check_type_hints(
        self,
        metrics: CodeQualityMetrics,
        stage: int = 1
    ) -> Tuple[bool, str, SuggestionPriority]:
        """Check type hints quality."""
        ratio = metrics.type_hints_ratio
        
        if stage < 2:
            threshold = 0.3
            priority = SuggestionPriority.LOW
        elif stage < 4:
            threshold = 0.6
            priority = SuggestionPriority.MEDIUM
        else:
            threshold = 0.85
            priority = SuggestionPriority.HIGH
        
        passed = ratio >= threshold
        message = f"Type hints: {ratio:.0%} (target: {threshold:.0%})"
        
        return passed, message, priority
    
    def check_docstrings(
        self,
        metrics: CodeQualityMetrics,
        stage: int = 1
    ) -> Tuple[bool, str, SuggestionPriority]:
        """Check documentation quality."""
        ratio = metrics.docstring_ratio
        
        if stage < 2:
            threshold = 0.2
            priority = SuggestionPriority.LOW
        elif stage < 4:
            threshold = 0.5
            priority = SuggestionPriority.MEDIUM
        else:
            threshold = 0.8
            priority = SuggestionPriority.HIGH
        
        passed = ratio >= threshold
        message = f"Documentation: {ratio:.0%} (target: {threshold:.0%})"
        
        return passed, message, priority
    
    def check_error_handling(
        self,
        metrics: CodeQualityMetrics,
        stage: int = 1
    ) -> Tuple[bool, str, SuggestionPriority]:
        """Check error handling."""
        ratio = metrics.error_handling_ratio
        
        if stage < 2:
            threshold = 0.0
            priority = SuggestionPriority.LOW
        elif stage < 3:
            threshold = 0.2
            priority = SuggestionPriority.MEDIUM
        else:
            threshold = 0.5
            priority = SuggestionPriority.HIGH
        
        passed = ratio >= threshold
        message = f"Error handling: {ratio:.0%} (target: {threshold:.0%})"
        
        return passed, message, priority
    
    def check_logging(
        self,
        metrics: CodeQualityMetrics,
        stage: int = 1
    ) -> Tuple[bool, str, SuggestionPriority]:
        """Check logging presence."""
        present = metrics.logging_presence >= 0.5
        
        if stage < 4:
            priority = SuggestionPriority.LOW
        else:
            priority = SuggestionPriority.HIGH
        
        message = f"Logging: {'✓' if present else '✗'} (stage {stage})"
        
        return present, message, priority
    
    def check_complexity(
        self,
        metrics: CodeQualityMetrics
    ) -> Tuple[bool, str, SuggestionPriority]:
        """Check code complexity."""
        complexity = metrics.cyclomatic_complexity
        
        if complexity <= 5:
            passed = True
            priority = SuggestionPriority.LOW
        elif complexity <= 10:
            passed = True
            priority = SuggestionPriority.MEDIUM
        elif complexity <= 15:
            passed = False
            priority = SuggestionPriority.HIGH
        else:
            passed = False
            priority = SuggestionPriority.CRITICAL
        
        message = f"Complexity: {complexity:.1f} (threshold: 10)"
        
        return passed, message, priority
    
    def check_code_style(
        self,
        metrics: CodeQualityMetrics
    ) -> Tuple[bool, str, SuggestionPriority]:
        """Check code style consistency."""
        consistency = metrics.consistency_score
        
        if consistency >= 0.9:
            passed = True
            priority = SuggestionPriority.LOW
        elif consistency >= 0.7:
            passed = True
            priority = SuggestionPriority.MEDIUM
        else:
            passed = False
            priority = SuggestionPriority.MEDIUM
        
        message = f"Consistency: {consistency:.0%}"
        
        return passed, message, priority
    
    def check_all(
        self,
        metrics: CodeQualityMetrics,
        stage: int = 1
    ) -> List[QualityGate]:
        """Run all quality checks."""
        gates = []
        
        # Type hints
        passed, msg, priority = self.check_type_hints(metrics, stage)
        gates.append(QualityGate(
            name="Type Hints",
            description=msg,
            threshold=0.7 if stage >= 2 else 0.3,
            current_value=metrics.type_hints_ratio,
            passed=passed,
            suggestion="Add type annotations to functions"
        ))
        
        # Docstrings
        passed, msg, priority = self.check_docstrings(metrics, stage)
        gates.append(QualityGate(
            name="Documentation",
            description=msg,
            threshold=0.6 if stage >= 2 else 0.2,
            current_value=metrics.docstring_ratio,
            passed=passed,
            suggestion="Add docstrings to public functions"
        ))
        
        # Error handling
        passed, msg, priority = self.check_error_handling(metrics, stage)
        gates.append(QualityGate(
            name="Error Handling",
            description=msg,
            threshold=0.5 if stage >= 3 else 0.2,
            current_value=metrics.error_handling_ratio,
            passed=passed,
            suggestion="Implement error handling"
        ))
        
        # Logging
        passed, msg, priority = self.check_logging(metrics, stage)
        gates.append(QualityGate(
            name="Logging",
            description=msg,
            threshold=0.5 if stage >= 4 else 0.0,
            current_value=metrics.logging_presence,
            passed=passed,
            suggestion="Add structured logging"
        ))
        
        # Complexity
        passed, msg, priority = self.check_complexity(metrics)
        gates.append(QualityGate(
            name="Complexity",
            description=msg,
            threshold=0.5,
            current_value=1.0 - min(metrics.cyclomatic_complexity / 20, 1.0),
            passed=passed,
            suggestion="Refactor complex functions"
        ))
        
        return gates
    
    def calculate_quality_score(
        self,
        metrics: CodeQualityMetrics,
        stage: int = 1
    ) -> float:
        """Calculate overall quality score 0-10."""
        gates = self.check_all(metrics, stage)
        
        # Weight gates by importance
        score = 0.0
        total_weight = 0.0
        
        weights = {
            "Type Hints": 1.5 if stage >= 2 else 0.5,
            "Documentation": 1.5,
            "Error Handling": 2.0,
            "Logging": 1.0 if stage >= 4 else 0.5,
            "Complexity": 2.0,
        }
        
        for gate in gates:
            weight = weights.get(gate.name, 1.0)
            gate_value = gate.current_value * 10 if gate.current_value <= 1.0 else 10.0
            score += gate_value * weight
            total_weight += weight
        
        if total_weight > 0:
            return min(10.0, max(1.0, score / total_weight))
        
        return 5.0
    
    def get_passed_checks(self, gates: List[QualityGate]) -> int:
        """Count passed quality checks."""
        return sum(1 for gate in gates if gate.passed)
    
    def get_failing_checks(self, gates: List[QualityGate]) -> List[QualityGate]:
        """Get failing quality checks."""
        return [gate for gate in gates if not gate.passed]
