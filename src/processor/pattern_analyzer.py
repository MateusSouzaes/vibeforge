"""Detect code patterns and architectural styles."""

import re
from pathlib import Path
from typing import List, Dict, Tuple
from src.processor.models import CodePattern


class PatternAnalyzer:
    """Detect code patterns and architectural conventions."""

    def __init__(self, repo_path: str):
        """Initialize analyzer.
        
        Args:
            repo_path: Path to repository
        """
        self.repo_path = Path(repo_path)

    def analyze_patterns(self) -> List[CodePattern]:
        """Analyze repository for code patterns.
        
        Returns:
            List of detected patterns
        """
        patterns = []
        
        patterns.extend(self._detect_architectural_patterns())
        patterns.extend(self._detect_design_patterns())
        patterns.extend(self._detect_testing_patterns())
        patterns.extend(self._detect_documentation_patterns())
        patterns.extend(self._detect_code_style_patterns())
        
        return patterns

    def _detect_architectural_patterns(self) -> List[CodePattern]:
        """Detect architectural patterns like MVC, layered architecture, etc.
        
        Returns:
            List of architectural patterns found
        """
        patterns = []
        folder_names = {p.name for p in self.repo_path.rglob("*") if p.is_dir()}
        
        # MVC Pattern
        if any(n in folder_names for n in ["views", "controllers", "models"]):
            patterns.append(CodePattern(
                name="MVC Architecture",
                description="Model-View-Controller pattern detected",
                frequency=1,
                examples=["views/", "controllers/", "models/"]
            ))
        
        # Layered Architecture
        if any(n in folder_names for n in ["api", "service", "domain", "infrastructure"]):
            patterns.append(CodePattern(
                name="Layered Architecture",
                description="Layered/onion architecture detected",
                frequency=1,
                examples=["api/", "service/", "domain/", "infrastructure/"]
            ))
        
        # Microservices
        if any(n in folder_names for n in ["services", "microservices"]):
            patterns.append(CodePattern(
                name="Microservices Structure",
                description="Microservices architecture pattern",
                frequency=1,
                examples=["services/"]
            ))
        
        # Plugin Architecture
        if any(n in folder_names for n in ["plugins", "extensions"]):
            patterns.append(CodePattern(
                name="Plugin Architecture",
                description="Plugin/extension architecture pattern",
                frequency=1,
                examples=["plugins/", "extensions/"]
            ))
        
        return patterns

    def _detect_design_patterns(self) -> List[CodePattern]:
        """Detect design patterns in code.
        
        Returns:
            List of design patterns found
        """
        patterns = []
        
        # Scan Python files for patterns
        py_files = list(self.repo_path.rglob("*.py"))
        
        if not py_files:
            return patterns
        
        # Factory Pattern
        factory_count = sum(1 for f in py_files if self._contains_pattern(f, r"class\s+\w+Factory|def\s+create_\w+"))
        if factory_count > 0:
            patterns.append(CodePattern(
                name="Factory Pattern",
                description="Factory design pattern detected",
                frequency=factory_count
            ))
        
        # Singleton Pattern
        singleton_count = sum(1 for f in py_files if self._contains_pattern(f, r"_instance|getInstance|@singleton"))
        if singleton_count > 0:
            patterns.append(CodePattern(
                name="Singleton Pattern",
                description="Singleton design pattern detected",
                frequency=singleton_count
            ))
        
        # Observer Pattern
        observer_count = sum(1 for f in py_files if self._contains_pattern(f, r"observer|listener|subscribe|publish"))
        if observer_count > 0:
            patterns.append(CodePattern(
                name="Observer Pattern",
                description="Observer/subscription pattern detected",
                frequency=observer_count
            ))
        
        # Strategy Pattern
        strategy_count = sum(1 for f in py_files if self._contains_pattern(f, r"strategy|Strategy"))
        if strategy_count > 0:
            patterns.append(CodePattern(
                name="Strategy Pattern",
                description="Strategy design pattern detected",
                frequency=strategy_count
            ))
        
        # Decorator Pattern
        decorator_count = sum(1 for f in py_files if self._contains_pattern(f, r"@property|@cached|@decorator"))
        if decorator_count > 0:
            patterns.append(CodePattern(
                name="Decorator Pattern",
                description="Decorator pattern detected",
                frequency=decorator_count
            ))
        
        return patterns

    def _detect_testing_patterns(self) -> List[CodePattern]:
        """Detect testing patterns and practices.
        
        Returns:
            List of testing patterns found
        """
        patterns = []
        
        # Unit Testing
        test_files = list(self.repo_path.rglob("test_*.py"))
        test_files.extend(self.repo_path.rglob("*_test.py"))
        
        if test_files:
            patterns.append(CodePattern(
                name="Unit Testing",
                description="Unit testing framework detected",
                frequency=len(test_files),
                examples=[f.name for f in test_files[:3]]
            ))
        
        # Integration Testing
        integration_files = list(self.repo_path.rglob("*integration*.py"))
        if integration_files:
            patterns.append(CodePattern(
                name="Integration Testing",
                description="Integration tests detected",
                frequency=len(integration_files)
            ))
        
        # BDD/Cucumber
        feature_files = list(self.repo_path.rglob("*.feature"))
        if feature_files:
            patterns.append(CodePattern(
                name="BDD Testing",
                description="Behavior-driven development (BDD) patterns",
                frequency=len(feature_files)
            ))
        
        return patterns

    def _detect_documentation_patterns(self) -> List[CodePattern]:
        """Detect documentation practices.
        
        Returns:
            List of documentation patterns found
        """
        patterns = []
        
        # Docstrings in Python
        py_files = list(self.repo_path.rglob("*.py"))
        docstring_count = sum(1 for f in py_files if self._contains_pattern(f, r'""".*?"""|\'\'\'.*?\'\'\''))
        
        if docstring_count > 3:
            patterns.append(CodePattern(
                name="Python Docstrings",
                description="Comprehensive docstring documentation",
                frequency=docstring_count
            ))
        
        # API Documentation
        if (self.repo_path / "docs").exists():
            patterns.append(CodePattern(
                name="API Documentation",
                description="Documentation directory found",
                frequency=1,
                examples=["docs/"]
            ))
        
        # README
        if (self.repo_path / "README.md").exists():
            patterns.append(CodePattern(
                name="README Documentation",
                description="Project README found",
                frequency=1
            ))
        
        # Architecture Decision Records
        if (self.repo_path / "docs" / "adr").exists():
            patterns.append(CodePattern(
                name="ADR (Architecture Decision Records)",
                description="Architectural decisions documented",
                frequency=1
            ))
        
        return patterns

    def _detect_code_style_patterns(self) -> List[CodePattern]:
        """Detect code style and quality patterns.
        
        Returns:
            List of code style patterns found
        """
        patterns = []
        
        # Type Hints (Python)
        py_files = list(self.repo_path.rglob("*.py"))
        typehint_count = sum(1 for f in py_files if self._contains_pattern(f, r":\s*(int|str|bool|float|List|Dict)|->"))
        
        if typehint_count > 2:
            patterns.append(CodePattern(
                name="Type Hints",
                description="Static type hints detected",
                frequency=typehint_count
            ))
        
        # Logging
        logging_count = sum(1 for f in py_files if self._contains_pattern(f, r"logger\.|log\.|logging\."))
        if logging_count > 0:
            patterns.append(CodePattern(
                name="Structured Logging",
                description="Logging framework usage detected",
                frequency=logging_count
            ))
        
        # Error Handling
        error_count = sum(1 for f in py_files if self._contains_pattern(f, r"except\s+\w+|try:|finally:|raise\s+\w+"))
        if error_count > 3:
            patterns.append(CodePattern(
                name="Comprehensive Error Handling",
                description="Explicit error handling patterns",
                frequency=error_count
            ))
        
        # Linting Config
        if (self.repo_path / ".pylintrc").exists() or (self.repo_path / ".flake8").exists():
            patterns.append(CodePattern(
                name="Code Linting",
                description="Code quality linting configured",
                frequency=1
            ))
        
        return patterns

    def _contains_pattern(self, filepath: Path, pattern: str) -> bool:
        """Check if file contains a regex pattern.
        
        Args:
            filepath: Path to file
            pattern: Regex pattern to search
            
        Returns:
            True if pattern found
        """
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            return bool(re.search(pattern, content, re.MULTILINE))
        except Exception:
            return False

    def get_pattern_summary(self, patterns: List[CodePattern]) -> Dict[str, int]:
        """Get summary of detected patterns.
        
        Args:
            patterns: List of detected patterns
            
        Returns:
            Dictionary with pattern counts
        """
        summary = {}
        for pattern in patterns:
            summary[pattern.name] = pattern.frequency
        
        return summary
