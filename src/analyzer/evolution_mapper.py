"""Map and identify evolution phases in project history."""

from typing import List, Optional
from datetime import datetime, timedelta
from src.analyzer.models import (
    AnalyzedCommit,
    CommitHistoryAnalysis,
    EvolutionPhase,
    DecisionType,
)


class EvolutionMapper:
    """Identify and map distinct phases in project evolution."""

    # Minimum days to constitute a phase
    MIN_PHASE_DURATION = 7
    
    # Minimum commits per phase
    MIN_PHASE_COMMITS = 2

    def __init__(self, phase_detection_days: int = 30):
        """Initialize evolution mapper.
        
        Args:
            phase_detection_days: Days to group commits into phases
        """
        self.phase_detection_days = phase_detection_days

    def map_phases(self, analysis: CommitHistoryAnalysis) -> List[EvolutionPhase]:
        """Map evolution phases from commit history.
        
        Args:
            analysis: Complete history analysis
            
        Returns:
            List of identified evolution phases
        """
        if not analysis.analyzed_commits:
            return []
        
        # Sort commits by date
        sorted_commits = sorted(analysis.analyzed_commits, key=lambda c: c.date)
        
        # Group commits into phases
        phases = []
        current_phase_commits = []
        current_phase_start = None
        
        for commit in sorted_commits:
            if current_phase_start is None:
                current_phase_start = commit.date
                current_phase_commits = [commit]
            else:
                # Check if commit is within phase window
                days_since_start = (commit.date - current_phase_start).days
                
                if days_since_start <= self.phase_detection_days:
                    current_phase_commits.append(commit)
                else:
                    # Start new phase
                    if len(current_phase_commits) >= self.MIN_PHASE_COMMITS:
                        phase = self._create_phase(current_phase_commits)
                        if phase:
                            phases.append(phase)
                    
                    current_phase_start = commit.date
                    current_phase_commits = [commit]
        
        # Don't forget last phase
        if len(current_phase_commits) >= self.MIN_PHASE_COMMITS:
            phase = self._create_phase(current_phase_commits)
            if phase:
                phases.append(phase)
        
        return phases

    def _create_phase(self, commits: List[AnalyzedCommit]) -> Optional[EvolutionPhase]:
        """Create an evolution phase from a group of commits.
        
        Args:
            commits: List of commits in this phase
            
        Returns:
            EvolutionPhase or None if invalid
        """
        if not commits:
            return None
        
        sorted_commits = sorted(commits, key=lambda c: c.date)
        start_date = sorted_commits[0].date
        end_date = sorted_commits[-1].date
        duration = (end_date - start_date).days + 1
        
        if duration < self.MIN_PHASE_DURATION and len(commits) < 5:
            return None
        
        # Determine primary focus
        primary_focus = self._determine_focus(commits)
        
        # Extract key decisions
        key_decisions = self._extract_key_decisions(commits)
        
        # Get unique contributors
        contributors = list(set(c.author.name for c in commits))
        
        # Generate phase name
        phase_name = self._generate_phase_name(primary_focus, start_date)
        
        return EvolutionPhase(
            name=phase_name,
            start_date=start_date,
            end_date=end_date,
            duration_days=duration,
            commit_count=len(commits),
            primary_focus=primary_focus,
            key_decisions=key_decisions,
            contributors=contributors,
        )

    def _determine_focus(self, commits: List[AnalyzedCommit]) -> str:
        """Determine primary focus of a phase.
        
        Args:
            commits: List of commits
            
        Returns:
            Primary focus description
        """
        # Count change types
        change_type_counts = {}
        for commit in commits:
            change_type = commit.change_pattern.change_type.value
            change_type_counts[change_type] = change_type_counts.get(change_type, 0) + 1
        
        # Find most common change type
        if change_type_counts:
            most_common = max(change_type_counts, key=change_type_counts.get)
            
            # Map to focus description
            focus_map = {
                "feature": "feature development",
                "test": "testing & quality",
                "refactor": "code refactoring",
                "bugfix": "bug fixes & maintenance",
                "docs": "documentation",
                "config": "configuration & setup",
                "breaking": "major refactoring",
                "chore": "maintenance tasks",
            }
            
            return focus_map.get(most_common, most_common)
        
        return "general development"

    def _extract_key_decisions(self, commits: List[AnalyzedCommit]) -> List[str]:
        """Extract significant decisions from commits.
        
        Args:
            commits: List of commits
            
        Returns:
            List of decision names
        """
        decisions = []
        
        for commit in commits:
            if commit.detected_decisions:
                for decision in commit.detected_decisions:
                    decisions.append(decision.name if hasattr(decision, 'name') else str(decision))
        
        return list(set(decisions))[:5]  # Top 5 unique decisions

    def _generate_phase_name(self, focus: str, start_date: datetime) -> str:
        """Generate a descriptive name for a phase.
        
        Args:
            focus: Primary focus of the phase
            start_date: Start date of phase
            
        Returns:
            Phase name
        """
        # Map focus to phase type
        phase_types = {
            "feature development": "Feature Sprint",
            "testing & quality": "QA & Stabilization",
            "code refactoring": "Refactoring Phase",
            "bug fixes & maintenance": "Maintenance Phase",
            "documentation": "Documentation Sprint",
            "configuration & setup": "Setup Phase",
            "major refactoring": "Major Redesign",
            "maintenance tasks": "Maintenance",
        }
        
        phase_type = phase_types.get(focus, "Development Phase")
        month = start_date.strftime("%b %Y")
        
        return f"{phase_type} ({month})"

    def identify_major_transitions(
        self,
        phases: List[EvolutionPhase]
    ) -> List[dict]:
        """Identify major transitions between phases.
        
        Args:
            phases: List of evolution phases
            
        Returns:
            List of transitions with details
        """
        transitions = []
        
        for i in range(len(phases) - 1):
            current_phase = phases[i]
            next_phase = phases[i + 1]
            
            # Check if focus changed significantly
            if current_phase.primary_focus != next_phase.primary_focus:
                transition = {
                    "from_phase": current_phase.name,
                    "to_phase": next_phase.name,
                    "focus_change": f"{current_phase.primary_focus} → {next_phase.primary_focus}",
                    "date": next_phase.start_date,
                    "days_since_last": (next_phase.start_date - current_phase.end_date).days,
                }
                transitions.append(transition)
        
        return transitions

    def estimate_maturity(self, analysis: CommitHistoryAnalysis) -> str:
        """Estimate project maturity based on evolution.
        
        Args:
            analysis: Complete history analysis
            
        Returns:
            Maturity level description
        """
        if analysis.total_commits < 10:
            return "Embryonic"
        
        if analysis.total_commits < 50:
            return "Early stage"
        
        if analysis.total_commits < 200:
            return "Growing"
        
        if analysis.total_commits < 500:
            return "Maturing"
        
        if analysis.total_commits < 1000:
            return "Mature"
        
        return "Production-grade"

    def calculate_velocity_trends(
        self,
        phases: List[EvolutionPhase]
    ) -> List[dict]:
        """Calculate commit velocity trends across phases.
        
        Args:
            phases: List of evolution phases
            
        Returns:
            Velocity metrics per phase
        """
        trends = []
        
        for phase in phases:
            velocity = phase.commit_count / max(phase.duration_days, 1)
            
            trend = {
                "phase": phase.name,
                "commits": phase.commit_count,
                "duration_days": phase.duration_days,
                "velocity": round(velocity, 2),  # commits per day
                "contributors": len(phase.contributors),
            }
            trends.append(trend)
        
        return trends

    def identify_critical_periods(
        self,
        analysis: CommitHistoryAnalysis
    ) -> List[dict]:
        """Identify critical periods (high activity, major changes).
        
        Args:
            analysis: Complete history analysis
            
        Returns:
            List of critical periods
        """
        critical_periods = []
        
        # Group commits by time period
        period_commits = {}
        
        for commit in analysis.analyzed_commits:
            period_key = commit.date.strftime("%Y-%m")
            if period_key not in period_commits:
                period_commits[period_key] = []
            period_commits[period_key].append(commit)
        
        # Find high-activity periods
        average_commits = len(analysis.analyzed_commits) / max(len(period_commits), 1)
        
        for period, commits in sorted(period_commits.items()):
            # High activity (above average)
            if len(commits) > average_commits * 1.5:
                # Count decision types
                significant_decisions = sum(
                    1 for c in commits
                    if c.detected_decisions
                )
                
                critical_periods.append({
                    "period": period,
                    "commit_count": len(commits),
                    "significant_decisions": significant_decisions,
                    "above_average": True,
                })
        
        return critical_periods

    def generate_evolution_summary(
        self,
        analysis: CommitHistoryAnalysis
    ) -> dict:
        """Generate a comprehensive evolution summary.
        
        Args:
            analysis: Complete history analysis
            
        Returns:
            Summary dictionary
        """
        phases = self.map_phases(analysis)
        transitions = self.identify_major_transitions(phases)
        maturity = self.estimate_maturity(analysis)
        velocity_trends = self.calculate_velocity_trends(phases)
        critical_periods = self.identify_critical_periods(analysis)
        
        return {
            "total_phases": len(phases),
            "phases": [self._phase_to_dict(p) for p in phases],
            "major_transitions": transitions,
            "project_maturity": maturity,
            "velocity_trends": velocity_trends,
            "critical_periods": critical_periods,
            "average_commits_per_phase": (
                analysis.total_commits / max(len(phases), 1)
            ),
        }

    @staticmethod
    def _phase_to_dict(phase: EvolutionPhase) -> dict:
        """Convert phase to dictionary.
        
        Args:
            phase: Evolution phase
            
        Returns:
            Dictionary representation
        """
        return {
            "name": phase.name,
            "start_date": phase.start_date.isoformat(),
            "end_date": phase.end_date.isoformat(),
            "duration_days": phase.duration_days,
            "commit_count": phase.commit_count,
            "primary_focus": phase.primary_focus,
            "key_decisions": phase.key_decisions,
            "contributors": phase.contributors,
        }
