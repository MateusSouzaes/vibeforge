"""Analyze and extract architectural decisions from commits."""

import re
from typing import List, Optional
from datetime import datetime
from src.analyzer.models import (
    Decision,
    DecisionType,
    AnalyzedCommit,
    CommitHistoryAnalysis,
)


class DecisionAnalyzer:
    """Extract architectural and technical decisions from commit history."""

    # Decision patterns based on conventional commits and keywords
    DECISION_PATTERNS = {
        DecisionType.ARCHITECTURE: [
            r"(?:refactor|redesign|restructure|architecture|rewrite).*(?:module|system|layer|component)",
            r"(?:implement|add|create).*(?:pattern|architecture|framework)",
            r"(?:migrate|move).*(?:to|from).*(?:new|pattern|structure)",
        ],
        DecisionType.DEPENDENCY: [
            r"(?:add|remove|upgrade|downgrade|switch).*(?:dependency|package|lib|framework)",
            r"(?:replace|update).*(?:with|to).*(?:package|library|framework)",
            r"(?:migrate).*(?:from|to).*(?:package|library)",
        ],
        DecisionType.PATTERN: [
            r"(?:implement|add|use|adopt).*(?:design pattern|pattern|strategy)",
            r"(?:factory|singleton|observer|strategy|decorator|adapter|builder)",
        ],
        DecisionType.CONSTRAINT: [
            r"(?:enforce|enforce|add).*(?:constraint|validation|rule|check)",
            r"(?:require|mandate|enforce).*(?:format|standard|rule)",
        ],
        DecisionType.REMOVAL: [
            r"(?:remove|delete|drop|deprecate).*(?:feature|module|code|functionality)",
            r"(?:deprecate|remove).*(?:support|compatibility)",
        ],
        DecisionType.MIGRATION: [
            r"(?:migrate|move|upgrade).*(?:from|to|version)",
            r"(?:upgrade|downgrade).*(?:version|framework|system)",
        ],
    }

    # Keywords that indicate significant decisions
    SIGNIFICANCE_KEYWORDS = [
        "breaking",
        "BREAKING",
        "major",
        "critical",
        "fundamental",
        "architectural",
        "redesign",
        "refactor",
        "migration",
        "upgrade",
    ]

    def __init__(self, min_significance: float = 0.3):
        """Initialize decision analyzer.
        
        Args:
            min_significance: Minimum significance score (0.0-1.0) to include decision
        """
        self.min_significance = min_significance

    def analyze_commits(self, commits: List[AnalyzedCommit]) -> List[Decision]:
        """Extract decisions from commits.
        
        Args:
            commits: List of analyzed commits
            
        Returns:
            List of extracted decisions
        """
        decisions = []
        
        for commit in commits:
            extracted = self._extract_from_commit(commit)
            decisions.extend(extracted)
        
        return decisions

    def _extract_from_commit(self, commit: AnalyzedCommit) -> List[Decision]:
        """Extract decisions from a single commit.
        
        Args:
            commit: Analyzed commit
            
        Returns:
            List of decisions found in commit
        """
        decisions = []
        message = commit.message.lower()
        
        for decision_type, patterns in self.DECISION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    significance = self._calculate_significance(commit)
                    
                    if significance >= self.min_significance:
                        decision = Decision(
                            name=self._extract_decision_name(commit),
                            description=commit.message,
                            decision_type=decision_type,
                            commit_hash=commit.hash,
                            commit_date=commit.date,
                            rationale=self._extract_rationale(commit),
                            impact_areas=self._extract_impact_areas(commit),
                        )
                        decisions.append(decision)
                        break  # Only extract once per decision type per commit
        
        return decisions

    def _extract_decision_name(self, commit: AnalyzedCommit) -> str:
        """Extract a concise decision name from commit.
        
        Args:
            commit: Analyzed commit
            
        Returns:
            Decision name
        """
        message = commit.message
        
        # Try to extract from conventional commit format
        if ":" in message:
            scope_subject = message.split(":", 1)[1].strip()
            if len(scope_subject) > 50:
                return scope_subject[:50] + "..."
            return scope_subject
        
        # Fallback to first line
        first_line = message.split("\n")[0]
        if len(first_line) > 50:
            return first_line[:50] + "..."
        return first_line

    def _extract_rationale(self, commit: AnalyzedCommit) -> Optional[str]:
        """Extract rationale/explanation from commit message.
        
        Args:
            commit: Analyzed commit
            
        Returns:
            Rationale text if found
        """
        lines = commit.message.split("\n")
        
        # Skip first line (conventional commit header)
        if len(lines) > 2:
            # Look for explanation after blank line
            body_start = None
            for i, line in enumerate(lines):
                if i > 0 and line.strip() == "":
                    body_start = i + 1
                    break
            
            if body_start:
                rationale = "\n".join(lines[body_start:])
                if rationale.strip():
                    return rationale.strip()[:200]  # Truncate to 200 chars
        
        return None

    def _extract_impact_areas(self, commit: AnalyzedCommit) -> List[str]:
        """Extract affected areas from changed files.
        
        Args:
            commit: Analyzed commit
            
        Returns:
            List of impacted areas
        """
        impact_areas = []
        extensions = commit.change_pattern.file_extensions
        
        # Map extensions to domains
        domain_map = {
            "py": "backend",
            "js": "frontend",
            "ts": "frontend",
            "tsx": "frontend",
            "jsx": "frontend",
            "rs": "backend",
            "go": "backend",
            "java": "backend",
            "cs": "backend",
            "sql": "database",
            "html": "frontend",
            "css": "styling",
            "scss": "styling",
            "json": "config",
            "yaml": "config",
            "yml": "config",
            "toml": "config",
            "md": "documentation",
            "test": "testing",
            "spec": "testing",
        }
        
        for ext in extensions:
            if ext in domain_map:
                area = domain_map[ext]
                if area not in impact_areas:
                    impact_areas.append(area)
        
        return impact_areas or ["general"]

    def _calculate_significance(self, commit: AnalyzedCommit) -> float:
        """Calculate significance score for a commit.
        
        Args:
            commit: Analyzed commit
            
        Returns:
            Significance score (0.0-1.0)
        """
        score = 0.5  # Base score
        message = commit.message.lower()
        
        # Increase score for breaking changes
        if "breaking" in message or "breaking change" in message:
            score = 0.95
        
        # Increase score for significant keywords
        for keyword in self.SIGNIFICANCE_KEYWORDS:
            if keyword.lower() in message:
                score = min(1.0, score + 0.1)
        
        # Increase score based on files changed
        if commit.change_pattern.file_count > 10:
            score = min(1.0, score + 0.15)
        
        # Increase score for large changes
        total_changes = (
            commit.change_pattern.added_lines 
            + commit.change_pattern.removed_lines
        )
        if total_changes > 500:
            score = min(1.0, score + 0.1)
        
        return score

    def detect_decision_patterns(
        self,
        analysis: CommitHistoryAnalysis
    ) -> dict:
        """Detect patterns in decisions over time.
        
        Args:
            analysis: Complete history analysis
            
        Returns:
            Dictionary with decision patterns
        """
        patterns = {
            "total_decisions": len(analysis.decisions),
            "by_type": self._count_by_type(analysis.decisions),
            "by_period": self._group_by_period(analysis.decisions),
            "decision_frequency": self._calculate_frequency(
                analysis.decisions,
                analysis.total_commits,
            ),
            "most_impacted_areas": self._find_most_impacted(analysis.decisions),
        }
        
        return patterns

    def _count_by_type(self, decisions: List[Decision]) -> dict:
        """Count decisions by type.
        
        Args:
            decisions: List of decisions
            
        Returns:
            Dict with counts
        """
        counts = {}
        for decision in decisions:
            decision_type = decision.decision_type.value
            counts[decision_type] = counts.get(decision_type, 0) + 1
        return counts

    def _group_by_period(self, decisions: List[Decision]) -> dict:
        """Group decisions by time period (months).
        
        Args:
            decisions: List of decisions
            
        Returns:
            Dict with period groupings
        """
        periods = {}
        for decision in decisions:
            period_key = decision.commit_date.strftime("%Y-%m")
            if period_key not in periods:
                periods[period_key] = []
            periods[period_key].append(decision.name)
        
        return periods

    def _calculate_frequency(
        self,
        decisions: List[Decision],
        total_commits: int
    ) -> float:
        """Calculate decision frequency ratio.
        
        Args:
            decisions: List of decisions
            total_commits: Total commits
            
        Returns:
            Frequency ratio
        """
        if total_commits == 0:
            return 0.0
        
        return len(decisions) / total_commits

    def _find_most_impacted(self, decisions: List[Decision]) -> List[str]:
        """Find areas most impacted by decisions.
        
        Args:
            decisions: List of decisions
            
        Returns:
            Top impacted areas
        """
        area_counts = {}
        
        for decision in decisions:
            for area in decision.impact_areas:
                area_counts[area] = area_counts.get(area, 0) + 1
        
        # Sort by count (descending)
        sorted_areas = sorted(area_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [area for area, count in sorted_areas[:5]]
