"""Roadmap generation engine - orchestrates all UC components."""

import logging
import os
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from uuid import uuid4
import json

from src.roadmap.models import (
    RoadmapPhase, PhaseItem, RoadmapPhaseInfo, ArchitecturalRoadmap,
    ProjectContext, ProjectAnalysisResult, ArchitecturalRecommendation,
    Recommendation, TechCategory, BestPractice, RoadmapConfig
)
from src.roadmap.analyzer import ArchitectureAnalyzer


logger = logging.getLogger(__name__)


class RoadmapGenerator:
    """Generates architectural roadmaps by integrating all UC modules."""
    
    def __init__(self):
        """Initialize roadmap generator with all components."""
        self.architecture_analyzer = ArchitectureAnalyzer()
        self.logger = logging.getLogger(__name__)
    
    def generate_roadmap(
        self,
        repository_path: str,
        config: Optional[RoadmapConfig] = None
    ) -> ArchitecturalRoadmap:
        """
        Generate complete architectural roadmap for a repository.
        
        Args:
            repository_path: Path to repository to analyze
            config: Optional roadmap configuration
            
        Returns:
            Complete architectural roadmap
        """
        if config is None:
            config = RoadmapConfig()
        config.validate()
        
        self.logger.info(f"Generating roadmap for {repository_path}")
        
        # Step 1: Build project context
        self.logger.info("Step 1: Analyzing code structure...")
        context = self._build_project_context(repository_path)
        
        # Step 2: Analyze architecture
        self.logger.info("Step 2: Analyzing architecture...")
        analysis = self.architecture_analyzer.analyze_context(context)
        
        # Step 3: Generate recommendations
        self.logger.info("Step 3: Generating recommendations...")
        recommendations = self._generate_recommendations(
            context, analysis, config
        )
        
        # Step 4: Suggest best practices
        self.logger.info("Step 4: Suggesting best practices...")
        best_practices = self.architecture_analyzer.suggest_best_practices(
            context, analysis
        )
        
        # Step 5: Generate roadmap phases
        self.logger.info("Step 5: Creating roadmap phases...")
        phases = self._create_roadmap_phases(
            context, recommendations, config
        )
        
        # Step 6: Assemble roadmap
        self.logger.info("Step 6: Assembling roadmap...")
        roadmap = ArchitecturalRoadmap(
            project_name=context.project_name,
            roadmap_id=str(uuid4()),
            context=context,
            analysis=analysis,
            recommendations=recommendations,
            phases=phases,
            best_practices=best_practices,
            quick_wins=self._identify_quick_wins(context, recommendations),
            long_term_vision=self._create_vision(context),
            next_90_days=self._create_90_day_plan(phases),
            risks_and_mitigation=self._identify_risks(context, analysis),
        )
        
        self.logger.info(f"Roadmap generated with {len(recommendations)} recommendations")
        return roadmap
    
    def _build_project_context(
        self,
        repository_path: str
    ) -> ProjectContext:
        """Build project context from analysis."""
        # Extract basic info from repository
        
        # Count code and test files
        code_files = 0
        test_files = 0
        for root, dirs, files in os.walk(repository_path):
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.java', '.go', '.rb', '.php')):
                    if any(x in file for x in ['test_', '_test.', '.test.', 'spec_']):
                        test_files += 1
                    else:
                        code_files += 1
        
        # Detect frameworks (basic heuristic)
        frameworks = self._detect_frameworks(repository_path)
        primary_lang = self._detect_primary_language(repository_path)
        
        return ProjectContext(
            project_name=os.path.basename(repository_path),
            repository_path=repository_path,
            primary_language=primary_lang,
            detected_frameworks=frameworks,
            total_code_files=code_files,
            total_test_files=test_files,
            test_coverage=self._estimate_test_coverage(test_files, code_files),
            code_complexity=self._estimate_complexity(code_files),
            technical_debt=0.3,
            project_age_days=30,
            contributors_count=1,
            last_commit_age_days=7,
        )
    
    def _detect_frameworks(self, repository_path: str) -> List[str]:
        """Detect frameworks used in project."""
        frameworks = []
        import os
        
        # Check for common indicators
        files = []
        for root, dirs, filenames in os.walk(repository_path):
            files.extend(filenames)
            break  # Only check root level for speed
        
        # Python frameworks
        if "requirements.txt" in files or "setup.py" in files:
            with open(os.path.join(repository_path, "requirements.txt"), "r") as f:
                content = f.read().lower()
                if "django" in content: frameworks.append("django")
                if "fastapi" in content: frameworks.append("fastapi")
                if "flask" in content: frameworks.append("flask")
                if "sqlalchemy" in content: frameworks.append("sqlalchemy")
        
        # JavaScript frameworks
        if "package.json" in files:
            import json
            try:
                with open(os.path.join(repository_path, "package.json"), "r") as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    if "react" in deps: frameworks.append("react")
                    if "nextjs" in deps or "next" in deps: frameworks.append("nextjs")
                    if "express" in deps: frameworks.append("express")
                    if "typescript" in deps: frameworks.append("typescript")
            except:
                pass
        
        # Docker/container
        if "Dockerfile" in files or "docker-compose.yml" in files:
            frameworks.append("docker")
        
        # Kubernetes
        if any(f.endswith(".yaml") for f in files if "k8s" in f.lower() or "kube" in f.lower()):
            frameworks.append("kubernetes")
        
        return frameworks
    
    def _detect_primary_language(self, repository_path: str) -> str:
        """Detect primary programming language."""
        import os
        
        lang_counts = {
            "python": 0,
            "javascript": 0,
            "typescript": 0,
            "java": 0,
            "go": 0,
            "ruby": 0,
            "csharp": 0,
            "cpp": 0,
        }
        
        extensions = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rb": "ruby",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".cc": "cpp",
        }
        
        for root, dirs, files in os.walk(repository_path):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext in extensions:
                    lang_counts[extensions[ext]] += 1
        
        primary = max(lang_counts, key=lang_counts.get)
        return primary if lang_counts[primary] > 0 else "unknown"
    
    def _estimate_test_coverage(self, test_files: int, code_files: int) -> float:
        """Estimate test coverage based on file counts."""
        if code_files == 0:
            return 0.0
        ratio = test_files / code_files
        return min(1.0, ratio * 0.8)  # Conservative estimate
    
    def _estimate_complexity(self, code_files: int) -> float:
        """Estimate code complexity."""
        if code_files < 10:
            return 3.0
        elif code_files < 50:
            return 6.0
        elif code_files < 200:
            return 8.5
        else:
            return 10.0
    
    def _generate_recommendations(
        self,
        context: ProjectContext,
        analysis: ProjectAnalysisResult,
        config: RoadmapConfig
    ) -> List[ArchitecturalRecommendation]:
        """Generate architectural recommendations."""
        recommendations = []
        
        # Detect anti-patterns
        anti_pattern_recs = self.architecture_analyzer.detect_anti_patterns(
            [], context
        )
        recommendations.extend(anti_pattern_recs)
        
        # Add category-specific recommendations
        if TechCategory.TESTING in config.focus_areas:
            if context.test_coverage < 0.80:
                recommendations.append(
                    ArchitecturalRecommendation(
                        title="Improve Test Coverage",
                        category=TechCategory.TESTING,
                        recommendation_type=Recommendation.IMPROVE,
                        description=f"Increase test coverage from {context.test_coverage:.1%} to 80%+",
                        why="Comprehensive tests reduce bugs and enable confident refactoring",
                        impact="Significant reduction in production issues",
                        effort="medium",
                        priority=8,
                        confidence_score=0.9,
                    )
                )
        
        if TechCategory.DOCUMENTATION in config.focus_areas:
            recommendations.append(
                ArchitecturalRecommendation(
                    title="Add Architecture Documentation",
                    category=TechCategory.DOCUMENTATION,
                    recommendation_type=Recommendation.IMPROVE,
                    description="Create ARCHITECTURE.md documenting design decisions and structure",
                    why="Documentation helps new contributors and clarifies design intent",
                    impact="Improved onboarding and knowledge sharing",
                    effort="low",
                    priority=6,
                    confidence_score=0.85,
                )
            )
        
        if TechCategory.DEPLOYMENT in config.focus_areas:
            if "docker" not in context.detected_frameworks:
                recommendations.append(
                    ArchitecturalRecommendation(
                        title="Containerize Application",
                        category=TechCategory.DEPLOYMENT,
                        recommendation_type=Recommendation.CONSIDER,
                        description="Create Dockerfile and docker-compose.yml for deployment",
                        why="Ensures consistency across environments",
                        impact="Simplified deployment and scaling",
                        effort="medium",
                        priority=7,
                        confidence_score=0.8,
                    )
                )
        
        # Sort by priority and filter
        recommendations.sort(key=lambda r: r.priority, reverse=True)
        recommendations = [
            r for r in recommendations
            if r.confidence_score >= config.min_confidence_threshold
        ][:config.max_recommendations]
        
        return recommendations
    
    def _create_roadmap_phases(
        self,
        context: ProjectContext,
        recommendations: List[ArchitecturalRecommendation],
        config: RoadmapConfig
    ) -> List[RoadmapPhaseInfo]:
        """Create roadmap phases."""
        phases = []
        
        # Foundation Phase
        phases.append(
            RoadmapPhaseInfo(
                phase=RoadmapPhase.FOUNDATION,
                title="Foundation & Structure",
                description="Establish solid architectural foundation",
                estimated_duration_weeks=4,
                items=[
                    PhaseItem(
                        title="Set up project structure",
                        description="Organize code into logical layers",
                        estimated_duration_weeks=1,
                    ),
                    PhaseItem(
                        title="Configure testing framework",
                        description="Set up unit and integration tests",
                        estimated_duration_weeks=1,
                    ),
                    PhaseItem(
                        title="Document architecture",
                        description="Create ARCHITECTURE.md and design docs",
                        estimated_duration_weeks=1,
                    ),
                ],
                expected_outcomes=[
                    "Clear project structure",
                    "Testing framework configured",
                    "Architecture documented",
                ],
            )
        )
        
        # MVP Phase
        if config.phases_to_generate >= 2:
            phases.append(
                RoadmapPhaseInfo(
                    phase=RoadmapPhase.MVP,
                    title="MVP & Core Features",
                    description="Develop minimum viable product",
                    estimated_duration_weeks=6,
                    prerequisites=[RoadmapPhase.FOUNDATION],
                    items=[
                        PhaseItem(
                            title="Implement core features",
                            description="Build essential functionality",
                            estimated_duration_weeks=3,
                        ),
                        PhaseItem(
                            title="Achieve 70%+ test coverage",
                            description="Add tests for core functionality",
                            estimated_duration_weeks=2,
                        ),
                    ],
                    expected_outcomes=[
                        "Working MVP",
                        "70%+ test coverage",
                        "Core features stable",
                    ],
                )
            )
        
        # Optimization Phase
        if config.phases_to_generate >= 3:
            phases.append(
                RoadmapPhaseInfo(
                    phase=RoadmapPhase.OPTIMIZATION,
                    title="Optimization & Polish",
                    description="Optimize performance and UX",
                    estimated_duration_weeks=4,
                    prerequisites=[RoadmapPhase.MVP],
                    items=[
                        PhaseItem(
                            title="Performance optimization",
                            description="Profile and optimize hot paths",
                            estimated_duration_weeks=2,
                        ),
                        PhaseItem(
                            title="Polish and refinement",
                            description="UX improvements and bug fixes",
                            estimated_duration_weeks=2,
                        ),
                    ],
                    expected_outcomes=[
                        "30% performance improvement",
                        "Improved UX",
                        "Better code quality",
                    ],
                )
            )
        
        # Scaling Phase
        if config.phases_to_generate >= 4:
            phases.append(
                RoadmapPhaseInfo(
                    phase=RoadmapPhase.SCALING,
                    title="Scaling & DevOps",
                    description="Prepare for production scale",
                    estimated_duration_weeks=6,
                    prerequisites=[RoadmapPhase.OPTIMIZATION],
                    items=[
                        PhaseItem(
                            title="Set up CI/CD",
                            description="Implement automated deployment",
                            estimated_duration_weeks=2,
                        ),
                        PhaseItem(
                            title="Add monitoring",
                            description="Set up logging and observability",
                            estimated_duration_weeks=2,
                        ),
                    ],
                    expected_outcomes=[
                        "CI/CD pipeline working",
                        "Monitoring configured",
                        "Ready for scale",
                    ],
                )
            )
        
        return phases
    
    def _identify_quick_wins(
        self,
        context: ProjectContext,
        recommendations: List[ArchitecturalRecommendation]
    ) -> List[str]:
        """Identify quick wins (low effort, high impact improvements)."""
        quick_wins = []
        
        # High priority, low effort items
        for rec in recommendations:
            if rec.effort == "low" and rec.priority >= 7:
                quick_wins.append(rec.title)
        
        return quick_wins[:5]
    
    def _create_vision(self, context: ProjectContext) -> str:
        """Create long-term vision statement."""
        return (
            f"Transform {context.project_name} into a well-architected, "
            f"maintainable {context.primary_language} project with comprehensive "
            f"testing, clear documentation, and scalable design patterns."
        )
    
    def _create_90_day_plan(self, phases: List[RoadmapPhaseInfo]) -> str:
        """Create 90-day plan summary."""
        if phases:
            first_phase = phases[0]
            return (
                f"Focus on {first_phase.title} by completing: "
                f"{', '.join(item.title for item in first_phase.items[:3])}"
            )
        return "Begin with foundation phase"
    
    def _identify_risks(
        self,
        context: ProjectContext,
        analysis: ProjectAnalysisResult
    ) -> Dict[str, str]:
        """Identify risks and mitigation strategies."""
        risks = {}
        
        if context.test_coverage < 0.30:
            risks["Low test coverage"] = (
                "High risk of regressions. Immediate action: Add unit tests "
                "for critical paths."
            )
        
        if context.code_complexity > 12:
            risks["High complexity"] = (
                "Difficult to maintain and modify. Consider refactoring "
                "into smaller modules."
            )
        
        if context.last_commit_age_days > 180:
            risks["Inactive project"] = (
                "Risk of stale dependencies. Schedule regular updates "
                "and maintenance."
            )
        
        if context.total_test_files == 0:
            risks["No tests"] = (
                "Critical: Start with integration tests for main flows, "
                "then add unit tests."
            )
        
        return risks
