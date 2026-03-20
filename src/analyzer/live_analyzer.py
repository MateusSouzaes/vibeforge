"""Live code analyzer - Main UC-007 implementation."""

import logging
import re
import ast
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from uuid import uuid4

from src.analyzer.live_analysis_models import (
    CodeQualityMetrics, PatternDeviation, CodeSuggestion,
    QualityGate, StageValidation, LiveAnalysisResult, 
    AnalyzedCode, CodeAnalysisRequest, AnalysisContext,
    QualityMetric, AnalysisStatus, SuggestionPriority
)


logger = logging.getLogger(__name__)


class LiveCodeAnalyzer:
    """Analyzes code in real-time against learned patterns."""
    
    # Stage expectations (what practices are important at each stage)
    STAGE_EXPECTATIONS = {
        1: [
            "project_structure",
            "basic_imports",
            "entry_point",
        ],
        2: [
            "function_definitions",
            "basic_docstrings",
            "type_hints",
        ],
        3: [
            "test_files",
            "error_handling",
            "configuration",
        ],
        4: [
            "ci_cd_config",
            "ci_cd_setup",
            "automated_tests",
        ],
        5: [
            "logging",
            "monitoring",
            "deployment",
        ],
        6: [
            "production_ready",
            "security",
            "scalability",
        ],
    }
    
    # Default learned patterns (adoption rates)
    DEFAULT_PATTERNS = {
        "uses_type_hints": 0.87,
        "has_docstrings": 0.82,
        "has_tests": 0.76,
        "has_error_handling": 0.71,
        "uses_logging": 0.68,
        "has_ci_cd": 0.64,
        "follows_pep8": 0.92,
        "has_comments": 0.55,
    }
    
    def __init__(self, context: Optional[AnalysisContext] = None):
        """Initialize analyzer."""
        self.context = context or self._create_default_context()
        self.logger = logging.getLogger(__name__)
    
    def analyze(self, request: CodeAnalysisRequest) -> LiveAnalysisResult:
        """
        Analyze code and generate recommendations.
        
        Args:
            request: Code analysis request
            
        Returns:
            Complete analysis result
        """
        request.validate()
        start = datetime.now()
        
        self.logger.info(f"Analyzing code for project {request.project_id}")
        
        # Parse and analyze code
        analyzed_code = self._analyze_code(request)
        
        # Detect deviations from patterns
        deviations = self._detect_deviations(
            analyzed_code, request.current_stage
        ) if request.include_deviations else []
        
        # Generate suggestions
        suggestions = self._generate_suggestions(
            deviations, request.current_stage
        ) if request.include_suggestions else []
        
        # Validate against stage
        stage_validation = self._validate_stage(
            analyzed_code, request.current_stage
        ) if request.include_stage_validation else None
        
        # Create quality gates
        gates = self._create_quality_gates(analyzed_code.metrics)
        
        # Calculate overall score
        overall_score = self._calculate_score(
            analyzed_code.metrics, deviations, len(gates)
        )
        
        # Determine status
        status = self._determine_status(overall_score, deviations)
        
        # Create next milestone
        next_milestone = self._get_next_milestone(
            request.current_stage, stage_validation
        )
        
        duration = (datetime.now() - start).total_seconds() * 1000
        
        result = LiveAnalysisResult(
            project_id=request.project_id,
            analysis_id=str(uuid4()),
            status=status,
            overall_score=overall_score,
            current_stage=request.current_stage,
            code_metrics=analyzed_code.metrics,
            deviations=deviations,
            suggestions=suggestions,
            quality_gates=gates,
            stage_validation=stage_validation,
            patterns_matched=sum(1 for s in suggestions 
                               if s.priority != SuggestionPriority.OPTIONAL),
            patterns_total=len(self.context.best_practices),
            next_milestone=next_milestone,
            urgent_fixes=[d.description for d in deviations 
                         if d.severity == SuggestionPriority.CRITICAL],
            improvements_available=[s.title for s in suggestions],
            analysis_duration_ms=duration,
        )
        
        self.logger.info(f"Analysis complete: {overall_score:.1f}/10.0")
        return result
    
    def _analyze_code(self, request: CodeAnalysisRequest) -> AnalyzedCode:
        """Analyze code and extract metrics."""
        code = request.code
        language = request.language
        
        if language == "python":
            metrics = self._analyze_python(code)
        elif language in ["javascript", "typescript"]:
            metrics = self._analyze_javascript(code)
        else:
            metrics = self._analyze_generic(code)
        
        return AnalyzedCode(
            project_id=request.project_id,
            code_snippet=code[:500],  # Store first 500 chars
            language=language,
            file_type=request.file_path.split(".")[-1] if request.file_path else "",
            metrics=metrics,
        )
    
    def _analyze_python(self, code: str) -> CodeQualityMetrics:
        """Analyze Python code."""
        metrics = CodeQualityMetrics()
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return metrics
        
        # Count lines
        lines = code.split("\n")
        total_lines = len(lines)
        
        # Type hints
        functions = [node for node in ast.walk(tree) 
                    if isinstance(node, ast.FunctionDef)]
        if functions:
            has_hints = sum(1 for f in functions 
                          if f.returns is not None or 
                          any(arg.annotation for arg in f.args.args))
            metrics.type_hints_ratio = has_hints / len(functions)
        
        # Docstrings
        with_docstrings = sum(
            1 for f in functions 
            if ast.get_docstring(f) is not None
        )
        if functions:
            metrics.docstring_ratio = with_docstrings / len(functions)
        
        # Error handling (try/except blocks)
        try_blocks = [node for node in ast.walk(tree) 
                     if isinstance(node, ast.Try)]
        if try_blocks and functions:
            metrics.error_handling_ratio = len(try_blocks) / len(functions)
        
        # Logging
        has_logging = "logging" in code or "logger" in code.lower()
        metrics.logging_presence = 1.0 if has_logging else 0.0
        
        # Comments
        comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
        if total_lines > 0:
            metrics.comment_density = min(1.0, comment_lines / total_lines)
        
        # Complexity (simplified)
        if_statements = len([n for n in ast.walk(tree) 
                           if isinstance(n, ast.If)])
        loops = len([n for n in ast.walk(tree) 
                    if isinstance(n, (ast.For, ast.While))])
        complexity = 1 + if_statements + loops
        metrics.cyclomatic_complexity = min(complexity, 20.0)  # Cap at 20
        
        return metrics
    
    def _analyze_javascript(self, code: str) -> CodeQualityMetrics:
        """Analyze JavaScript/TypeScript code."""
        metrics = CodeQualityMetrics()
        
        lines = code.split("\n")
        
        # Type hints (TypeScript)
        type_lines = sum(1 for line in lines 
                        if ":" in line and ("string" in line or "number" in line))
        if lines:
            metrics.type_hints_ratio = min(type_lines / len(lines), 1.0)
        
        # JSDoc/Comments
        jsdoc_lines = sum(1 for line in lines 
                         if "/**" in line or "//" in line)
        if lines:
            metrics.comment_density = min(jsdoc_lines / len(lines), 1.0)
        
        # Error handling
        try_catch = sum(1 for line in lines 
                       if "try" in line or "catch" in line)
        metrics.error_handling_ratio = min(try_catch / max(len(lines), 1), 1.0)
        
        # Logging
        has_logging = any("console" in line or "logger" in line 
                        for line in lines)
        metrics.logging_presence = 1.0 if has_logging else 0.0
        
        return metrics
    
    def _analyze_generic(self, code: str) -> CodeQualityMetrics:
        """Generic code analysis."""
        metrics = CodeQualityMetrics()
        
        lines = code.split("\n")
        
        # Comments
        comment_lines = sum(1 for line in lines 
                          if line.strip().startswith("#") or 
                          line.strip().startswith("//"))
        metrics.comment_density = min(
            comment_lines / max(len(lines), 1), 1.0
        )
        
        # Error handling (generic keywords)
        error_lines = sum(1 for line in lines 
                        if any(kw in line.lower() 
                             for kw in ["except", "catch", "error", "try"]))
        metrics.error_handling_ratio = min(
            error_lines / max(len(lines), 1), 1.0
        )
        
        return metrics
    
    def _detect_deviations(
        self, 
        code: AnalyzedCode,
        current_stage: int
    ) -> List[PatternDeviation]:
        """Detect deviations from learned patterns."""
        deviations = []
        metrics = code.metrics
        
        # Type hints deviation
        if metrics.type_hints_ratio < 0.7:
            adoption = self.context.learned_patterns.get(
                "uses_type_hints", 0.87
            )
            deviations.append(
                PatternDeviation(
                    pattern_type="missing_type_hints",
                    description=f"Type hints coverage is {metrics.type_hints_ratio:.0%}",
                    severity=SuggestionPriority.HIGH if current_stage >= 2 else SuggestionPriority.MEDIUM,
                    frequency_in_repos=adoption,
                    your_score=metrics.type_hints_ratio,
                    target_score=0.9,
                    improvement_needed=0.9 - metrics.type_hints_ratio,
                    example_code="def greet(name: str) -> str:\n    return f'Hello {name}'",
                    related_patterns=["docstrings", "error_handling"],
                )
            )
        
        # Docstrings deviation
        if metrics.docstring_ratio < 0.6:
            deviations.append(
                PatternDeviation(
                    pattern_type="missing_docstrings",
                    description=f"Documentation coverage is {metrics.docstring_ratio:.0%}",
                    severity=SuggestionPriority.MEDIUM,
                    frequency_in_repos=self.context.learned_patterns.get(
                        "has_docstrings", 0.82
                    ),
                    your_score=metrics.docstring_ratio,
                    target_score=0.8,
                    improvement_needed=0.8 - metrics.docstring_ratio,
                )
            )
        
        # Error handling deviation
        if metrics.error_handling_ratio < 0.3:
            deviations.append(
                PatternDeviation(
                    pattern_type="insufficient_error_handling",
                    description="Error handling is insufficient",
                    severity=SuggestionPriority.HIGH,
                    frequency_in_repos=self.context.learned_patterns.get(
                        "has_error_handling", 0.71
                    ),
                    your_score=metrics.error_handling_ratio,
                    target_score=0.7,
                    improvement_needed=0.7 - metrics.error_handling_ratio,
                )
            )
        
        # Logging deviation
        if metrics.logging_presence < 0.5 and current_stage >= 4:
            deviations.append(
                PatternDeviation(
                    pattern_type="missing_logging",
                    description="Logging not configured",
                    severity=SuggestionPriority.MEDIUM,
                    frequency_in_repos=self.context.learned_patterns.get(
                        "uses_logging", 0.68
                    ),
                    your_score=metrics.logging_presence,
                    target_score=1.0,
                    improvement_needed=1.0 - metrics.logging_presence,
                )
            )
        
        # Code complexity
        if code.metrics.cyclomatic_complexity > 10:
            deviations.append(
                PatternDeviation(
                    pattern_type="high_complexity",
                    description=f"Cyclomatic complexity: {code.metrics.cyclomatic_complexity:.1f}",
                    severity=SuggestionPriority.HIGH,
                    frequency_in_repos=0.3,
                    your_score=1.0 - min(code.metrics.cyclomatic_complexity / 20, 1.0),
                    target_score=0.8,
                    improvement_needed=0.8 - (1.0 - min(code.metrics.cyclomatic_complexity / 20, 1.0)),
                )
            )
        
        return deviations
    
    def _generate_suggestions(
        self,
        deviations: List[PatternDeviation],
        current_stage: int
    ) -> List[CodeSuggestion]:
        """Generate suggestions from deviations."""
        suggestions = []
        
        for dev in deviations:
            if dev.pattern_type == "missing_type_hints":
                suggestions.append(
                    CodeSuggestion(
                        title="Add Type Hints",
                        description="Type hints improve code clarity and enable IDE support",
                        priority=dev.severity,
                        practice_adoption_rate=dev.frequency_in_repos,
                        action_required=f"Add type hints to reach {dev.target_score:.0%}",
                        expected_benefit="Better IDE support, fewer runtime errors",
                        example_implementation="def process(data: list) -> dict:\n    return {}",
                        estimated_effort="low",
                        related_metric=QualityMetric.TYPE_HINTS,
                    )
                )
            
            elif dev.pattern_type == "missing_docstrings":
                suggestions.append(
                    CodeSuggestion(
                        title="Document Functions",
                        description="Docstrings help other developers understand code",
                        priority=dev.severity,
                        practice_adoption_rate=dev.frequency_in_repos,
                        action_required=f"Add docstrings to reach {dev.target_score:.0%}",
                        expected_benefit="Better maintainability and knowledge sharing",
                        estimated_effort="low",
                        related_metric=QualityMetric.DOCSTRINGS,
                    )
                )
            
            elif dev.pattern_type == "insufficient_error_handling":
                suggestions.append(
                    CodeSuggestion(
                        title="Improve Error Handling",
                        description="Proper error handling prevents crashes and improves UX",
                        priority=dev.severity,
                        practice_adoption_rate=dev.frequency_in_repos,
                        action_required="Add try/except blocks or error checks",
                        expected_benefit="More robust and production-ready code",
                        estimated_effort="medium",
                        related_metric=QualityMetric.ERROR_HANDLING,
                    )
                )
            
            elif dev.pattern_type == "missing_logging":
                suggestions.append(
                    CodeSuggestion(
                        title="Add Structured Logging",
                        description="Logging helps debug issues in production",
                        priority=dev.severity,
                        practice_adoption_rate=dev.frequency_in_repos,
                        action_required="Integrate logging library and add log statements",
                        expected_benefit="Better observability and debugging",
                        estimated_effort="medium",
                        related_metric=QualityMetric.LOGGING,
                    )
                )
            
            elif dev.pattern_type == "high_complexity":
                suggestions.append(
                    CodeSuggestion(
                        title="Reduce Code Complexity",
                        description="High complexity makes code hard to maintain",
                        priority=dev.severity,
                        practice_adoption_rate=0.6,
                        action_required="Refactor complex functions into smaller ones",
                        expected_benefit="Easier to test, maintain, and understand",
                        estimated_effort="high",
                        related_metric=QualityMetric.CODE_COMPLEXITY,
                    )
                )
        
        return suggestions
    
    def _create_quality_gates(
        self,
        metrics: CodeQualityMetrics
    ) -> List[QualityGate]:
        """Create quality gates."""
        gates = [
            QualityGate(
                name="Type Hints Coverage",
                description="At least 70% of functions have type hints",
                threshold=0.7,
                current_value=metrics.type_hints_ratio,
                passed=metrics.type_hints_ratio >= 0.7,
                suggestion="Add type hints to more functions",
            ),
            QualityGate(
                name="Documentation Coverage",
                description="At least 60% of functions are documented",
                threshold=0.6,
                current_value=metrics.docstring_ratio,
                passed=metrics.docstring_ratio >= 0.6,
                suggestion="Add docstrings to functions",
            ),
            QualityGate(
                name="Error Handling",
                description="Proper error handling in functions",
                threshold=0.3,
                current_value=metrics.error_handling_ratio,
                passed=metrics.error_handling_ratio >= 0.3,
                suggestion="Add try/except blocks",
            ),
            QualityGate(
                name="Code Complexity",
                description="Cyclomatic complexity below 10",
                threshold=0.5,
                current_value=1.0 - min(metrics.cyclomatic_complexity / 20, 1.0),
                passed=metrics.cyclomatic_complexity <= 10,
                suggestion="Refactor to reduce complexity",
            ),
        ]
        
        return gates
    
    def _validate_stage(
        self,
        code: AnalyzedCode,
        current_stage: int
    ) -> StageValidation:
        """Validate code against stage expectations."""
        expected = self.STAGE_EXPECTATIONS.get(current_stage, [])
        
        # Check which practices are present
        aligned = []
        missing = []
        
        for practice in expected:
            if self._has_practice(code, practice):
                aligned.append(practice)
            else:
                missing.append(practice)
        
        alignment = len(aligned) / max(len(expected), 1)
        
        return StageValidation(
            current_stage=current_stage,
            stage_name=f"Stage {current_stage}",
            expected_practices=expected,
            missing_practices=missing,
            aligned_practices=aligned,
            overall_alignment=alignment,
        )
    
    def _has_practice(self, code: AnalyzedCode, practice: str) -> bool:
        """Check if code has a specific practice."""
        metrics = code.metrics
        
        if practice == "type_hints":
            return metrics.type_hints_ratio >= 0.5
        elif practice == "basic_docstrings":
            return metrics.docstring_ratio >= 0.3
        elif practice == "error_handling":
            return metrics.error_handling_ratio >= 0.2
        elif practice == "logging":
            return metrics.logging_presence >= 0.5
        elif practice == "ci_cd_config":
            return True  # Would check for CI config files
        
        return False
    
    def _calculate_score(
        self,
        metrics: CodeQualityMetrics,
        deviations: List[PatternDeviation],
        gates_count: int
    ) -> float:
        """Calculate overall score 0-10."""
        # Base score from metrics
        base_scores = [
            metrics.type_hints_ratio * 1.5,
            metrics.docstring_ratio * 1.5,
            metrics.error_handling_ratio * 2.0,
            metrics.logging_presence * 1.0,
            (1.0 - min(metrics.cyclomatic_complexity / 20, 1.0)) * 2.0,
            metrics.comment_density * 1.0,
        ]
        
        base_score = sum(base_scores) / len(base_scores) * 10
        
        # Penalties
        deviation_penalty = len([d for d in deviations 
                               if d.severity == SuggestionPriority.CRITICAL]) * 2
        deviation_penalty += len([d for d in deviations 
                                if d.severity == SuggestionPriority.HIGH]) * 1
        
        final_score = max(1.0, base_score - deviation_penalty)
        return min(10.0, final_score)
    
    def _determine_status(
        self,
        score: float,
        deviations: List[PatternDeviation]
    ) -> AnalysisStatus:
        """Determine analysis status."""
        critical = sum(1 for d in deviations 
                      if d.severity == SuggestionPriority.CRITICAL)
        
        if critical > 0:
            return AnalysisStatus.AT_RISK
        elif score >= 8.5:
            return AnalysisStatus.EXCELLENT
        elif score >= 7.0:
            return AnalysisStatus.ON_TRACK
        else:
            return AnalysisStatus.NEEDS_IMPROVEMENT
    
    def _get_next_milestone(
        self,
        current_stage: int,
        stage_validation: Optional[StageValidation]
    ) -> str:
        """Get next milestone."""
        next_stage = min(current_stage + 1, 6)
        
        if stage_validation and stage_validation.missing_practices:
            practices = ", ".join(stage_validation.missing_practices[:2])
            return f"Complete {practices} for Stage {current_stage}"
        
        return f"Move to Stage {next_stage}"
    
    def _create_default_context(self) -> AnalysisContext:
        """Create default analysis context."""
        return AnalysisContext(
            learned_patterns=self.DEFAULT_PATTERNS,
            stage_expectations=self.STAGE_EXPECTATIONS,
            best_practices={
                "uses_type_hints": "Use type hints for all functions",
                "has_docstrings": "Document public functions and classes",
                "has_tests": "Write unit tests for code",
                "has_error_handling": "Handle errors gracefully",
                "uses_logging": "Use structured logging",
                "has_ci_cd": "Set up CI/CD pipeline",
                "follows_pep8": "Follow code style guide",
                "has_comments": "Include comments for complex logic",
            },
        )
