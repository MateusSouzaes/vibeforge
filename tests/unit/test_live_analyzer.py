"""Tests for UC-007 Live Code Analysis."""

import pytest
from datetime import datetime

from src.analyzer.live_analysis_models import (
    QualityMetric, AnalysisStatus, SuggestionPriority,
    CodeQualityMetrics, PatternDeviation, CodeSuggestion,
    QualityGate, StageValidation, LiveAnalysisResult,
    AnalyzedCode, CodeAnalysisRequest, AnalysisContext,
)
from src.analyzer.live_analyzer import LiveCodeAnalyzer
from src.analyzer.quality_checker import QualityChecker


class TestQualityMetric:
    """Test QualityMetric enum."""
    
    def test_all_metrics_exist(self):
        """Test all quality metrics are defined."""
        assert QualityMetric.TYPE_HINTS.value == "type_hints"
        assert QualityMetric.DOCSTRINGS.value == "docstrings"
        assert QualityMetric.TEST_COVERAGE.value == "test_coverage"
        assert QualityMetric.CODE_COMPLEXITY.value == "code_complexity"
        assert QualityMetric.LOGGING.value == "logging"


class TestAnalysisStatus:
    """Test AnalysisStatus enum."""
    
    def test_status_values(self):
        """Test status values."""
        assert AnalysisStatus.ON_TRACK.value == "on_track"
        assert AnalysisStatus.NEEDS_IMPROVEMENT.value == "needs_improvement"
        assert AnalysisStatus.AT_RISK.value == "at_risk"
        assert AnalysisStatus.EXCELLENT.value == "excellent"


class TestCodeQualityMetrics:
    """Test CodeQualityMetrics model."""
    
    def test_default_metrics(self):
        """Test default metric values."""
        metrics = CodeQualityMetrics()
        
        assert metrics.type_hints_ratio == 0.0
        assert metrics.docstring_ratio == 0.0
        assert metrics.test_coverage == 0.0
        assert metrics.cyclomatic_complexity == 10.0
    
    def test_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = CodeQualityMetrics(
            type_hints_ratio=0.8,
            docstring_ratio=0.7,
            test_coverage=0.85,
        )
        
        d = metrics.to_dict()
        
        assert d["type_hints"] == 0.8
        assert d["docstrings"] == 0.7
        assert d["test_coverage"] == 0.85
        assert len(d) == 8


class TestPatternDeviation:
    """Test PatternDeviation model."""
    
    def test_create_deviation(self):
        """Create a pattern deviation."""
        dev = PatternDeviation(
            pattern_type="missing_type_hints",
            description="Missing type hints",
            severity=SuggestionPriority.HIGH,
            frequency_in_repos=0.87,
            your_score=0.5,
            target_score=0.9,
            improvement_needed=0.4,
        )
        
        assert dev.pattern_type == "missing_type_hints"
        assert dev.severity == SuggestionPriority.HIGH
        assert dev.improvement_needed == 0.4
    
    def test_deviation_with_example(self):
        """Create deviation with example code."""
        dev = PatternDeviation(
            pattern_type="missing_docstrings",
            description="Missing docstrings",
            severity=SuggestionPriority.MEDIUM,
            frequency_in_repos=0.82,
            your_score=0.3,
            target_score=0.8,
            improvement_needed=0.5,
            example_code="def greet():\n    return 'hello'",
        )
        
        assert dev.example_code is not None
        assert "def" in dev.example_code


class TestCodeSuggestion:
    """Test CodeSuggestion model."""
    
    def test_create_suggestion(self):
        """Create code suggestion."""
        sugg = CodeSuggestion(
            title="Add Type Hints",
            description="Improves code clarity",
            priority=SuggestionPriority.HIGH,
            practice_adoption_rate=0.87,
            action_required="Add type hints",
            expected_benefit="Better IDE support",
        )
        
        assert sugg.title == "Add Type Hints"
        assert sugg.priority == SuggestionPriority.HIGH
        assert sugg.estimated_effort == "low"


class TestQualityGate:
    """Test QualityGate model."""
    
    def test_quality_gate_passed(self):
        """Test quality gate that passed."""
        gate = QualityGate(
            name="Type Hints",
            description="Type hints coverage",
            threshold=0.7,
            current_value=0.85,
            passed=True,
        )
        
        assert gate.passed is True
        assert gate.current_value >= gate.threshold
    
    def test_quality_gate_failed(self):
        """Test quality gate that failed."""
        gate = QualityGate(
            name="Documentation",
            description="Doc coverage",
            threshold=0.8,
            current_value=0.4,
            passed=False,
        )
        
        assert gate.passed is False
        assert gate.current_value < gate.threshold


class TestStageValidation:
    """Test StageValidation model."""
    
    def test_validation_on_track(self):
        """Test validation when on track."""
        validation = StageValidation(
            current_stage=2,
            stage_name="Stage 2",
            expected_practices=["type_hints", "docstrings"],
            missing_practices=["docstrings"],
            aligned_practices=["type_hints"],
            overall_alignment=0.5,
        )
        
        assert validation.current_stage == 2
        assert len(validation.aligned_practices) == 1
        assert len(validation.missing_practices) == 1


class TestLiveAnalysisResult:
    """Test LiveAnalysisResult model."""
    
    def test_create_result(self):
        """Create analysis result."""
        metrics = CodeQualityMetrics(
            type_hints_ratio=0.8,
            docstring_ratio=0.7,
        )
        
        result = LiveAnalysisResult(
            project_id="test-proj",
            analysis_id="analysis-123",
            status=AnalysisStatus.ON_TRACK,
            overall_score=8.2,
            current_stage=2,
            code_metrics=metrics,
        )
        
        assert result.project_id == "test-proj"
        assert result.overall_score == 8.2
        assert result.is_on_track is True
    
    def test_result_pattern_alignment(self):
        """Test pattern alignment calculation."""
        result = LiveAnalysisResult(
            project_id="test",
            analysis_id="id",
            status=AnalysisStatus.ON_TRACK,
            overall_score=8.0,
            current_stage=1,
            code_metrics=CodeQualityMetrics(),
            patterns_matched=8,
            patterns_total=10,
        )
        
        assert result.pattern_alignment == 80.0
    
    def test_result_critical_issues(self):
        """Test counting critical issues."""
        dev1 = PatternDeviation(
            pattern_type="test1",
            description="Issue 1",
            severity=SuggestionPriority.CRITICAL,
            frequency_in_repos=0.5,
            your_score=0.0,
            target_score=1.0,
            improvement_needed=1.0,
        )
        dev2 = PatternDeviation(
            pattern_type="test2",
            description="Issue 2",
            severity=SuggestionPriority.HIGH,
            frequency_in_repos=0.5,
            your_score=0.0,
            target_score=1.0,
            improvement_needed=1.0,
        )
        
        result = LiveAnalysisResult(
            project_id="test",
            analysis_id="id",
            status=AnalysisStatus.AT_RISK,
            overall_score=5.0,
            current_stage=1,
            code_metrics=CodeQualityMetrics(),
            deviations=[dev1, dev2],
        )
        
        assert result.critical_issues_count == 1


class TestCodeAnalysisRequest:
    """Test CodeAnalysisRequest model."""
    
    def test_valid_request(self):
        """Create valid analysis request."""
        request = CodeAnalysisRequest(
            project_id="proj-123",
            code="print('hello')",
            language="python",
            current_stage=2,
        )
        
        request.validate()  # Should not raise
        assert request.project_id == "proj-123"
    
    def test_invalid_project_id(self):
        """Test validation with missing project ID."""
        request = CodeAnalysisRequest(
            project_id="",
            code="code",
        )
        
        with pytest.raises(ValueError):
            request.validate()
    
    def test_invalid_code(self):
        """Test validation with missing code."""
        request = CodeAnalysisRequest(
            project_id="test",
            code="",
        )
        
        with pytest.raises(ValueError):
            request.validate()
    
    def test_invalid_stage(self):
        """Test validation with invalid stage."""
        request = CodeAnalysisRequest(
            project_id="test",
            code="code",
            current_stage=10,  # Invalid
        )
        
        with pytest.raises(ValueError):
            request.validate()


class TestLiveCodeAnalyzer:
    """Test LiveCodeAnalyzer."""
    
    def test_create_analyzer(self):
        """Create analyzer instance."""
        analyzer = LiveCodeAnalyzer()
        
        assert analyzer is not None
        assert analyzer.context is not None
        assert len(analyzer.STAGE_EXPECTATIONS) == 6
    
    def test_analyze_python_code(self):
        """Analyze Python code."""
        analyzer = LiveCodeAnalyzer()
        
        code = """
def greet(name: str) -> str:
    '''Greet someone.'''
    return f'Hello {name}'

def process(data):
    try:
        return data.upper()
    except:
        pass
"""
        
        request = CodeAnalysisRequest(
            project_id="test",
            code=code,
            language="python",
            current_stage=2,
        )
        
        result = analyzer.analyze(request)
        
        assert result.project_id == "test"
        assert result.overall_score > 0
        assert result.status in [
            AnalysisStatus.ON_TRACK,
            AnalysisStatus.EXCELLENT,
            AnalysisStatus.NEEDS_IMPROVEMENT,
            AnalysisStatus.AT_RISK,
        ]
    
    def test_analyze_code_without_type_hints(self):
        """Analyze code missing type hints."""
        analyzer = LiveCodeAnalyzer()
        
        code = """
def add(a, b):
    return a + b

def multiply(x, y):
    return x * y
"""
        
        request = CodeAnalysisRequest(
            project_id="test",
            code=code,
            language="python",
            current_stage=2,
        )
        
        result = analyzer.analyze(request)
        
        # Should have deviation for missing type hints
        assert sum(1 for d in result.deviations 
                  if "type_hints" in d.pattern_type) > 0
    
    def test_analyze_code_with_high_complexity(self):
        """Analyze code with high complexity."""
        analyzer = LiveCodeAnalyzer()
        
        code = """
def complex_function(x):
    if x > 0:
        if x > 10:
            if x > 100:
                if x > 1000:
                    if x > 10000:
                        if x > 100000:
                            if x > 1000000:
                                if x > 10000000:
                                    for i in range(10):
                                        if i > 5:
                                            return "very high"
    return "low"
"""
        
        request = CodeAnalysisRequest(
            project_id="test",
            code=code,
            language="python",
            current_stage=3,
        )
        
        result = analyzer.analyze(request)
        
        # Should detect high complexity
        assert any(d.pattern_type == "high_complexity" 
                  for d in result.deviations)
    
    def test_analyze_javascript_code(self):
        """Analyze JavaScript code."""
        analyzer = LiveCodeAnalyzer()
        
        code = """
const greet = (name) => {
    return `Hello ${name}`;
};

async function fetchData() {
    try {
        const response = await fetch('/api');
        return response.json();
    } catch (err) {
        console.error(err);
    }
}
"""
        
        request = CodeAnalysisRequest(
            project_id="test",
            code=code,
            language="javascript",
            current_stage=2,
        )
        
        result = analyzer.analyze(request)
        
        assert result.project_id == "test"
        assert result.code_metrics is not None
    
    def test_suggestions_generated(self):
        """Test that suggestions are generated."""
        analyzer = LiveCodeAnalyzer()
        
        code = "print('hello')"
        
        request = CodeAnalysisRequest(
            project_id="test",
            code=code,
            language="python",
            current_stage=2,
        )
        
        result = analyzer.analyze(request)
        
        assert len(result.suggestions) > 0
        for sugg in result.suggestions:
            assert sugg.title is not None
            assert sugg.priority is not None
    
    def test_quality_gates_created(self):
        """Test quality gates are created."""
        analyzer = LiveCodeAnalyzer()
        
        code = "def func(): pass"
        
        request = CodeAnalysisRequest(
            project_id="test",
            code=code,
            language="python",
            current_stage=2,
        )
        
        result = analyzer.analyze(request)
        
        assert len(result.quality_gates) > 0
        assert all(isinstance(g, QualityGate) for g in result.quality_gates)
    
    def test_stage_validation(self):
        """Test stage validation."""
        analyzer = LiveCodeAnalyzer()
        
        code = """
def greet(name: str) -> str:
    '''Greet.'''
    return f'Hello {name}'
"""
        
        request = CodeAnalysisRequest(
            project_id="test",
            code=code,
            language="python",
            current_stage=2,
        )
        
        result = analyzer.analyze(request)
        
        assert result.stage_validation is not None
        assert result.stage_validation.current_stage == 2


class TestQualityChecker:
    """Test QualityChecker."""
    
    def test_create_checker(self):
        """Create quality checker."""
        checker = QualityChecker()
        
        assert checker is not None
    
    def test_check_type_hints_stage_1(self):
        """Check type hints at stage 1."""
        checker = QualityChecker()
        metrics = CodeQualityMetrics(type_hints_ratio=0.2)
        
        passed, msg, priority = checker.check_type_hints(metrics, stage=1)
        
        assert "Type hints" in msg
        assert priority is not None
    
    def test_check_type_hints_stage_4(self):
        """Check type hints at stage 4 (stricter)."""
        checker = QualityChecker()
        metrics_low = CodeQualityMetrics(type_hints_ratio=0.5)
        metrics_high = CodeQualityMetrics(type_hints_ratio=0.9)
        
        passed_low, _, _ = checker.check_type_hints(metrics_low, stage=4)
        passed_high, _, _ = checker.check_type_hints(metrics_high, stage=4)
        
        assert passed_low is False
        assert passed_high is True
    
    def test_check_all_quality_gates(self):
        """Test checking all quality gates."""
        checker = QualityChecker()
        metrics = CodeQualityMetrics(
            type_hints_ratio=0.8,
            docstring_ratio=0.7,
            error_handling_ratio=0.6,
            logging_presence=0.5,
        )
        
        gates = checker.check_all(metrics, stage=2)
        
        assert len(gates) >= 4
        assert all(isinstance(g, QualityGate) for g in gates)
    
    def test_quality_score_calculation(self):
        """Test quality score calculation."""
        checker = QualityChecker()
        metrics = CodeQualityMetrics(
            type_hints_ratio=0.8,
            docstring_ratio=0.7,
            error_handling_ratio=0.6,
            cyclomatic_complexity=5.0,
        )
        
        score = checker.calculate_quality_score(metrics, stage=2)
        
        assert 0.0 <= score <= 10.0
        assert score > 5.0  # Good metrics should score well
    
    def test_passed_checks_count(self):
        """Test counting passed checks."""
        checker = QualityChecker()
        gates = [
            QualityGate("test1", "desc", 0.5, 0.8, True),
            QualityGate("test2", "desc", 0.5, 0.3, False),
            QualityGate("test3", "desc", 0.5, 0.9, True),
        ]
        
        passed = checker.get_passed_checks(gates)
        
        assert passed == 2
    
    def test_failing_checks(self):
        """Test getting failing checks."""
        checker = QualityChecker()
        gates = [
            QualityGate("test1", "desc", 0.5, 0.8, True),
            QualityGate("test2", "desc", 0.5, 0.3, False),
            QualityGate("test3", "desc", 0.5, 0.2, False),
        ]
        
        failing = checker.get_failing_checks(gates)
        
        assert len(failing) == 2
        assert all(not g.passed for g in failing)


class TestIntegration:
    """Integration tests."""
    
    def test_end_to_end_analysis(self):
        """Test complete end-to-end analysis."""
        analyzer = LiveCodeAnalyzer()
        checker = QualityChecker()
        
        code = """
def calculate(x: int, y: int) -> int:
    '''Calculate sum.'''
    try:
        return x + y
    except TypeError:
        return 0
"""
        
        request = CodeAnalysisRequest(
            project_id="myapp",
            code=code,
            language="python",
            current_stage=3,
        )
        
        result = analyzer.analyze(request)
        score = checker.calculate_quality_score(result.code_metrics, stage=3)
        
        assert result.overall_score > 0
        assert score > 0
        # Code has type hints, docstring, and error handling - should be good
        assert result.status in [AnalysisStatus.ON_TRACK, AnalysisStatus.EXCELLENT]
    
    def test_multiple_analyses(self):
        """Test analyzing multiple code snippets."""
        analyzer = LiveCodeAnalyzer()
        
        codes = [
            "print('hello')",
            "def func(): pass",
            "class MyClass:\n    def method(self): pass",
        ]
        
        results = []
        for i, code in enumerate(codes):
            request = CodeAnalysisRequest(
                project_id=f"test-{i}",
                code=code,
                language="python",
                current_stage=1,
            )
            results.append(analyzer.analyze(request))
        
        assert len(results) == 3
        assert all(r.project_id.startswith("test-") for r in results)
        assert all(r.overall_score > 0 for r in results)
