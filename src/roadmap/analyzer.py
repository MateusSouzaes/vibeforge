"""Architecture analysis engine."""

from typing import List, Dict, Set, Optional, Tuple
import logging

from src.roadmap.models import (
    ProjectContext, ProjectAnalysisResult, ArchitecturalRecommendation,
    Recommendation, TechCategory, BestPractice
)


logger = logging.getLogger(__name__)


class ArchitectureAnalyzer:
    """Analyzes project architecture and identifies improvement opportunities."""
    
    # Known anti-patterns and bad practices
    ANTI_PATTERNS = {
        "god_object": {
            "name": "God Object/Class",
            "description": "Class doing too much (high complexity/high LOC)",
            "threshold": {"complexity": 15, "lines": 500},
            "recommendation": Recommendation.AVOID,
        },
        "code_duplication": {
            "name": "Code Duplication",
            "description": "High code duplication across modules",
            "threshold": {"duplication_ratio": 0.15},
            "recommendation": Recommendation.IMPROVE,
        },
        "no_tests": {
            "name": "Missing Tests",
            "description": "Low or no test coverage",
            "threshold": {"coverage": 0.30},
            "recommendation": Recommendation.IMPROVE,
        },
        "poor_documentation": {
            "name": "Poor Documentation",
            "description": "Missing README, inline docs, or architecture docs",
            "threshold": {"doc_ratio": 0.05},
            "recommendation": Recommendation.IMPROVE,
        },
        "loose_coupling": {
            "name": "Tight Coupling",
            "description": "High interdependency between modules",
            "threshold": {"coupling": 0.7},
            "recommendation": Recommendation.IMPROVE,
        },
    }
    
    # Known best practices
    BEST_PRACTICES = {
        "layered_architecture": {
            "title": "Layered Architecture",
            "description": "Organize code into logical layers (presentation, business, data)",
            "benefits": ["Separation of concerns", "Testability", "Maintainability"],
            "for_languages": ["python", "java", "csharp", "javascript"],
        },
        "dependency_injection": {
            "title": "Dependency Injection",
            "description": "Inject dependencies rather than creating them internally",
            "benefits": ["Testability", "Loose coupling", "Flexibility"],
            "for_languages": ["python", "java", "csharp", "javascript"],
        },
        "comprehensive_testing": {
            "title": "Comprehensive Testing",
            "description": "Maintain >80% code coverage with unit, integration, and E2E tests",
            "benefits": ["Confidence in changes", "Catch regressions", "Document behavior"],
            "for_languages": ["all"],
        },
        "ci_cd": {
            "title": "CI/CD Pipeline",
            "description": "Automate build, test, and deployment",
            "benefits": ["Fast feedback", "Reduce human error", "Enable frequent releases"],
            "for_languages": ["all"],
        },
        "documentation_as_code": {
            "title": "Documentation as Code",
            "description": "Keep architecture, API docs alongside code",
            "benefits": ["Up-to-date docs", "Version control", "Single source of truth"],
            "for_languages": ["all"],
        },
        "error_handling": {
            "title": "Proper Error Handling",
            "description": "Comprehensive error handling and logging",
            "benefits": ["Debugging ease", "Production readiness", "User experience"],
            "for_languages": ["all"],
        },
        "configuration_management": {
            "title": "Configuration Management",
            "description": "Externalize configuration (env vars, config files)",
            "benefits": ["Environment flexibility", "Secret management", "12 Factor App"],
            "for_languages": ["all"],
        },
        "design_patterns": {
            "title": "Design Patterns",
            "description": "Apply appropriate design patterns (Factory, Strategy, etc)",
            "benefits": ["Code reusability", "Proven solutions", "Team communication"],
            "for_languages": ["all"],
        },
    }
    
    def __init__(self):
        """Initialize analyzer."""
        self.logger = logging.getLogger(__name__)
    
    def analyze_context(self, context: ProjectContext) -> ProjectAnalysisResult:
        """Analyze project context and calculate scores."""
        result = ProjectAnalysisResult(context=context)
        
        # Calculate architecture score based on framework usage
        result.architecture_score = self._score_architecture(context)
        
        # Calculate test score
        result.test_score = self._score_tests(context)
        
        # Calculate documentation score (basic heuristic)
        result.documentation_score = 5.0  # Baseline
        
        # Calculate security score
        result.security_score = self._score_security(context)
        
        # Calculate maintainability score
        result.maintainability_score = self._score_maintainability(context)
        
        # Calculate scalability score
        result.scalability_score = self._score_scalability(context)
        
        return result
    
    def _score_architecture(self, context: ProjectContext) -> float:
        """Score architecture based on framework choices."""
        score = 5.0
        
        # Bonus for using recognized frameworks
        if context.primary_language == "python":
            if any(f in context.detected_frameworks for f in ["django", "fastapi", "flask"]):
                score += 2.0
        elif context.primary_language == "javascript":
            if any(f in context.detected_frameworks for f in ["react", "nextjs", "express"]):
                score += 2.0
        
        # Bonus for microservices indicators
        if any(f in context.detected_frameworks for f in ["grpc", "kafka", "rabbitmq"]):
            score += 1.5
        
        # Adjust based on code complexity
        if context.code_complexity > 10:
            score -= 1.5
        elif context.code_complexity < 3:
            score += 1.0
        
        return min(10.0, max(1.0, score))
    
    def _score_tests(self, context: ProjectContext) -> float:
        """Score testing based on test coverage and test count."""
        if context.total_test_files == 0:
            return 2.0
        
        # High weight on coverage
        coverage_score = context.test_coverage * 10.0
        
        # Weight on test count
        test_ratio = context.total_test_files / max(context.total_code_files, 1)
        test_score = min(3.0, test_ratio * 10.0)
        
        return min(10.0, coverage_score * 0.7 + test_score * 0.3)
    
    def _score_security(self, context: ProjectContext) -> float:
        """Score security practices."""
        score = 5.0
        
        # Bonus for frameworks with built-in security
        if context.primary_language == "python":
            if "django" in context.detected_frameworks:
                score += 2.0
            elif "fastapi" in context.detected_frameworks:
                score += 1.5
        
        # Penalty if no testing (no security testing)
        if context.test_coverage < 0.30:
            score -= 2.0
        
        return min(10.0, max(1.0, score))
    
    def _score_maintainability(self, context: ProjectContext) -> float:
        """Score maintainability."""
        score = 5.0
        
        # Bonus for reasonable complexity
        if 5 <= context.code_complexity <= 10:
            score += 2.0
        elif context.code_complexity < 5:
            score += 1.5
        elif context.code_complexity > 15:
            score -= 2.5
        
        # Bonus for active project
        if context.last_commit_age_days < 7:
            score += 1.0
        
        return min(10.0, max(1.0, score))
    
    def _score_scalability(self, context: ProjectContext) -> float:
        """Score scalability potential."""
        score = 5.0
        
        # Bonus for async/scalable frameworks
        if context.primary_language == "python":
            if any(f in context.detected_frameworks for f in ["fastapi", "async"]):
                score += 2.0
        elif context.primary_language == "go":
            score += 1.5
        
        # Bonus for recent tech
        if any(f in context.detected_frameworks for f in ["kubernetes", "docker", "grpc"]):
            score += 2.5
        
        return min(10.0, max(1.0, score))
    
    def detect_anti_patterns(
        self, 
        patterns: List[CodePattern],
        context: ProjectContext
    ) -> List[ArchitecturalRecommendation]:
        """Detect anti-patterns in code."""
        recommendations = []
        
        # Check for god objects (high complexity code)
        if context.code_complexity > self.ANTI_PATTERNS["god_object"]["threshold"]["complexity"]:
            recommendations.append(
                ArchitecturalRecommendation(
                    title="God Object Pattern Detected",
                    category=TechCategory.PATTERNS,
                    recommendation_type=Recommendation.AVOID,
                    description="High complexity detected in core modules. Consider breaking into smaller, focused classes.",
                    why="God objects are hard to maintain, test, and understand",
                    impact="Improved testability and maintainability",
                    effort="medium",
                    priority=8,
                    confidence_score=0.85,
                )
            )
        
        # Check for no tests
        if context.test_coverage < self.ANTI_PATTERNS["no_tests"]["threshold"]["coverage"]:
            recommendations.append(
                ArchitecturalRecommendation(
                    title="Low Test Coverage",
                    category=TechCategory.TESTING,
                    recommendation_type=Recommendation.IMPROVE,
                    description=f"Test coverage is {context.test_coverage:.1%}. Target should be >80%.",
                    why="Low coverage increases risk of bugs in production",
                    impact="Increased confidence in code changes",
                    effort="medium",
                    priority=9,
                    confidence_score=0.95,
                )
            )
        
        # Check for no tests files
        if context.total_test_files == 0:
            recommendations.append(
                ArchitecturalRecommendation(
                    title="Missing Test Suite",
                    category=TechCategory.TESTING,
                    recommendation_type=Recommendation.IMPROVE,
                    description="No test files detected. Start with unit tests for core functionality.",
                    why="Tests provide confidence, document behavior, and catch regressions",
                    impact="Significantly improved code reliability",
                    effort="high",
                    priority=10,
                    confidence_score=0.98,
                )
            )
        
        return recommendations
    
    def suggest_best_practices(
        self,
        context: ProjectContext,
        analysis: ProjectAnalysisResult
    ) -> List[BestPractice]:
        """Suggest applicable best practices."""
        practices = []
        
        # Layered architecture for larger projects
        if context.total_code_files > 50:
            practices.append(
                BestPractice(
                    title=self.BEST_PRACTICES["layered_architecture"]["title"],
                    category=TechCategory.ARCHITECTURE,
                    description=self.BEST_PRACTICES["layered_architecture"]["description"],
                    benefits=self.BEST_PRACTICES["layered_architecture"]["benefits"],
                    is_currently_applied=False,
                )
            )
        
        # DI for complex projects
        if context.code_complexity > 8:
            practices.append(
                BestPractice(
                    title=self.BEST_PRACTICES["dependency_injection"]["title"],
                    category=TechCategory.PATTERNS,
                    description=self.BEST_PRACTICES["dependency_injection"]["description"],
                    benefits=self.BEST_PRACTICES["dependency_injection"]["benefits"],
                    is_currently_applied=False,
                )
            )
        
        # Testing best practices
        if context.test_coverage < 0.80:
            practices.append(
                BestPractice(
                    title=self.BEST_PRACTICES["comprehensive_testing"]["title"],
                    category=TechCategory.TESTING,
                    description=self.BEST_PRACTICES["comprehensive_testing"]["description"],
                    benefits=self.BEST_PRACTICES["comprehensive_testing"]["benefits"],
                    is_currently_applied=False,
                    confidence_score=0.95,
                )
            )
        
        # CI/CD for projects with multiple files
        if context.total_code_files > 10:
            practices.append(
                BestPractice(
                    title=self.BEST_PRACTICES["ci_cd"]["title"],
                    category=TechCategory.DEPLOYMENT,
                    description=self.BEST_PRACTICES["ci_cd"]["description"],
                    benefits=self.BEST_PRACTICES["ci_cd"]["benefits"],
                    is_currently_applied=False,
                )
            )
        
        return practices
    
    def calculate_technical_debt(self, context: ProjectContext) -> float:
        """Calculate technical debt score (0.0-1.0, higher = more debt)."""
        debt = 0.0
        
        # High complexity = debt
        if context.code_complexity > 10:
            debt += (context.code_complexity - 10) * 0.01
        
        # Low test coverage = debt
        debt += (1.0 - context.test_coverage) * 0.3
        
        # No tests = significant debt
        if context.total_test_files == 0:
            debt += 0.4
        
        return min(1.0, debt)
