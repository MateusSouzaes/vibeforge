"""Extract commit information from git repositories."""

import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from src.analyzer.models import (
    CommitAuthor,
    ChangePattern,
    ChangeType,
    AnalyzedCommit,
    CommitHistoryAnalysis,
)


class CommitExtractor:
    """Extract and parse git commit history."""

    def __init__(self, repo_path: str):
        """Initialize commit extractor.
        
        Args:
            repo_path: Path to git repository
            
        Raises:
            ValueError: If directory is not a git repository
        """
        self.repo_path = Path(repo_path)
        
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"{repo_path} is not a git repository")

    def extract_all_commits(self) -> List[Dict]:
        """Extract all commits from repository.
        
        Returns:
            List of commit information dictionaries
        """
        try:
            # Get all commits with detailed info
            cmd = [
                "git",
                "-C", str(self.repo_path),
                "log",
                "--all",
                "--format=%H|%s|%an|%ae|%ai|%b",
                "--numstat",
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"git log failed: {result.stderr}")
            
            commits = self._parse_git_log(result.stdout)
            return commits
            
        except Exception as e:
            raise RuntimeError(f"Failed to extract commits: {e}")

    def _parse_git_log(self, output: str) -> List[Dict]:
        """Parse git log output.
        
        Args:
            output: Raw git log output
            
        Returns:
            List of commit dictionaries
        """
        commits = []
        lines = output.strip().split("\n")
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines
            if not line.strip():
                i += 1
                continue
            
            # Parse commit header (hash|subject|author|email|date|body)
            if "|" in line:
                parts = line.split("|", 5)
                if len(parts) >= 5:
                    try:
                        commit = {
                            "hash": parts[0],
                            "subject": parts[1],
                            "author": parts[2],
                            "email": parts[3],
                            "date": self._parse_date(parts[4]),
                            "body": parts[5] if len(parts) > 5 else "",
                            "files_changed": 0,
                            "additions": 0,
                            "deletions": 0,
                        }
                        commits.append(commit)
                    except (IndexError, ValueError):
                        pass
            
            i += 1
        
        return commits

    def _parse_date(self, date_str: str) -> datetime:
        """Parse git date string.
        
        Args:
            date_str: Date from git (e.g. '2024-01-15 10:30:45 +0100')
            
        Returns:
            Parsed datetime
        """
        try:
            # Split by space first, then take date and time part
            # Format: "2024-01-15 10:30:45 +0100"
            parts = date_str.split()
            if len(parts) >= 2:
                date_part = parts[0]
                time_part = parts[1] if len(parts) > 1 else "00:00:00"
                return datetime.fromisoformat(f"{date_part}T{time_part}")
            return datetime.fromisoformat(date_str)
        except Exception:
            return datetime.now()

    def get_commit_stats(self, commit_hash: str) -> Optional[ChangePattern]:
        """Get detailed stats for a specific commit.
        
        Args:
            commit_hash: Git commit hash
            
        Returns:
            ChangePattern with file statistics or None
        """
        try:
            cmd = [
                "git",
                "-C", str(self.repo_path),
                "show",
                "--stat",
                "--format=",
                commit_hash,
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            # Parse stat output
            added_lines = 0
            removed_lines = 0
            file_count = 0
            file_extensions = []
            
            for line in result.stdout.split("\n"):
                if "|" in line and ("+" in line or "-" in line):
                    file_count += 1
                    # Extract file extension
                    file_path = line.split("|")[0].strip()
                    if "." in file_path:
                        ext = file_path.split(".")[-1]
                        if ext not in file_extensions:
                            file_extensions.append(ext)
                    
                    # Count changes
                    changes = line.split("|")[1]
                    additions = changes.count("+")
                    deletions = changes.count("-")
                    added_lines += additions
                    removed_lines += deletions
            
            change_type = self._infer_change_type(added_lines, removed_lines, file_extensions)
            
            return ChangePattern(
                file_count=file_count,
                added_lines=added_lines,
                removed_lines=removed_lines,
                modified_lines=file_count,
                file_extensions=file_extensions,
                change_type=change_type,
            )
            
        except Exception:
            return None

    def _infer_change_type(
        self,
        additions: int,
        deletions: int,
        extensions: List[str]
    ) -> ChangeType:
        """Infer change type from statistics.
        
        Args:
            additions: Lines added
            deletions: Lines removed
            extensions: File extensions changed
            
        Returns:
            Inferred ChangeType
        """
        # Test files
        if any(ext in ["test", "spec"] for ext in extensions):
            return ChangeType.TEST
        
        # Docs
        if any(ext in ["md", "txt", "rst"] for ext in extensions):
            return ChangeType.DOCS
        
        # Config
        if any(ext in ["json", "yml", "yaml", "toml", "ini"] for ext in extensions):
            return ChangeType.CONFIG
        
        # Refactor (few additions, many deletions)
        if deletions > additions * 2:
            return ChangeType.REFACTOR
        
        # Feature (many additions)
        if additions > deletions:
            return ChangeType.FEATURE
        
        return ChangeType.CHORE

    def get_contributors(self) -> List[CommitAuthor]:
        """Get list of contributors with statistics.
        
        Returns:
            List of CommitAuthor objects
        """
        try:
            cmd = [
                "git",
                "-C", str(self.repo_path),
                "log",
                "--all",
                "--format=%an|%ae",
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return []
            
            contributors_dict: Dict[str, CommitAuthor] = {}
            
            for line in result.stdout.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|")
                    name = parts[0]
                    email = parts[1] if len(parts) > 1 else ""
                    
                    if email not in contributors_dict:
                        contributors_dict[email] = CommitAuthor(
                            name=name,
                            email=email,
                            commits_count=0,
                        )
                    
                    contributors_dict[email].commits_count += 1
            
            return list(contributors_dict.values())
            
        except Exception:
            return []

    def get_repo_name(self) -> str:
        """Get repository name from path.
        
        Returns:
            Repository name
        """
        return self.repo_path.name

    def extract_history_analysis(self) -> CommitHistoryAnalysis:
        """Extract complete commit history analysis.
        
        Returns:
            CommitHistoryAnalysis with full repository history
        """
        # Extract commits
        commits = self.extract_all_commits()
        contributors = self.get_contributors()
        
        # Analyze each commit
        analyzed_commits = []
        for commit in commits:
            stats = self.get_commit_stats(commit["hash"])
            if stats is None:
                stats = ChangePattern(0, 0, 0, 0, [], ChangeType.CHORE)
            
            author_obj = next(
                (c for c in contributors if c.email == commit.get("email", "")),
                CommitAuthor(name=commit.get("author", ""), email=""),
            )
            
            analyzed = AnalyzedCommit(
                hash=commit["hash"],
                message=commit["subject"],
                author=author_obj,
                date=commit["date"],
                change_pattern=stats,
                detected_decisions=[],
                related_commits=[],
                significance_score=0.5,
            )
            analyzed_commits.append(analyzed)
        
        # Calculate date range
        if analyzed_commits:
            dates = [c.date for c in analyzed_commits]
            start_date = min(dates)
            end_date = max(dates)
            duration = (end_date - start_date).days
        else:
            start_date = datetime.now()
            end_date = datetime.now()
            duration = 0
        
        return CommitHistoryAnalysis(
            repository_name=self.get_repo_name(),
            total_commits=len(analyzed_commits),
            date_range_start=start_date,
            date_range_end=end_date,
            duration_days=duration,
            contributors=contributors,
            analyzed_commits=analyzed_commits,
            decisions=[],
            evolution_phases=[],
            commit_patterns={},
        )
