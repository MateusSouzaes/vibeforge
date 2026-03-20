"""Code structure parser for multiple programming languages."""

from pathlib import Path
from typing import Dict, List, Set
from src.processor.models import (
    LanguageType,
    FileMetadata,
    ProjectStructure,
    ParsedProject,
)


class CodeParser:
    """Parse code structure and extract metadata."""

    # Language file extensions
    LANGUAGE_EXTENSIONS: Dict[str, LanguageType] = {
        ".py": LanguageType.PYTHON,
        ".js": LanguageType.JAVASCRIPT,
        ".jsx": LanguageType.JAVASCRIPT,
        ".ts": LanguageType.TYPESCRIPT,
        ".tsx": LanguageType.TYPESCRIPT,
        ".rs": LanguageType.RUST,
        ".go": LanguageType.GO,
        ".java": LanguageType.JAVA,
        ".cs": LanguageType.CSHARP,
    }

    # Test file patterns
    TEST_PATTERNS = {".test.", ".spec.", "test_", "_test.py", "tests/"}

    def __init__(self, repo_path: str):
        """Initialize parser with repository path.
        
        Args:
            repo_path: Path to the repository to parse
        """
        self.repo_path = Path(repo_path)
        self.repo_name = self.repo_path.name

    def parse(self) -> ParsedProject:
        """Parse the entire project.
        
        Returns:
            ParsedProject with all extracted information
        """
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {self.repo_path}")

        files = self._scan_files()
        structure = self._analyze_structure(files)
        primary_lang = self._determine_primary_language(files)

        return ParsedProject(
            repository_name=self.repo_name,
            primary_language=primary_lang,
            structure=structure,
            files=files,
            has_dockerfile=self._has_dockerfile(),
            has_ci_cd=self._has_ci_cd(),
            has_makefile=self._has_makefile(),
            config_files=self._find_config_files(),
        )

    def _scan_files(self) -> List[FileMetadata]:
        """Scan repository and collect file metadata.
        
        Returns:
            List of FileMetadata for all code files
        """
        files = []
        
        for path in self.repo_path.rglob("*"):
            if not path.is_file():
                continue
                
            # Skip hidden and common non-code files
            if any(part.startswith(".") for part in path.relative_to(self.repo_path).parts):
                continue
            if path.name.startswith("."):
                continue

            suffix = path.suffix.lower()
            if suffix not in self.LANGUAGE_EXTENSIONS:
                continue

            language = self.LANGUAGE_EXTENSIONS[suffix]
            is_test = self._is_test_file(str(path))
            loc = self._count_lines(path)

            files.append(
                FileMetadata(
                    path=str(path.relative_to(self.repo_path)),
                    language=language,
                    lines_of_code=loc,
                    has_tests=is_test,
                )
            )

        return files

    def _analyze_structure(self, files: List[FileMetadata]) -> ProjectStructure:
        """Analyze project structure from files.
        
        Args:
            files: List of file metadata
            
        Returns:
            ProjectStructure with analysis
        """
        language_count: Dict[str, int] = {}
        folders: Set[str] = set()

        for file in files:
            lang = file.language.value
            language_count[lang] = language_count.get(lang, 0) + 1

            # Extract top-level folder
            parts = file.path.split("/")
            if len(parts) > 1:
                folders.add(parts[0])

        return ProjectStructure(
            total_files=len(files),
            languages=language_count,
            main_folders=sorted(list(folders)),
        )

    def _determine_primary_language(self, files: List[FileMetadata]) -> LanguageType:
        """Determine the primary language by file count.
        
        Args:
            files: List of file metadata
            
        Returns:
            Most common LanguageType
        """
        if not files:
            return LanguageType.PYTHON  # Default

        lang_count: Dict[LanguageType, int] = {}
        for file in files:
            if not file.has_tests:  # Exclude test files
                lang_count[file.language] = lang_count.get(file.language, 0) + 1

        return max(lang_count, key=lang_count.get) if lang_count else LanguageType.PYTHON

    def _count_lines(self, filepath: Path) -> int:
        """Count lines of code in a file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Number of lines
        """
        try:
            return len(filepath.read_text(encoding="utf-8", errors="ignore").splitlines())
        except Exception:
            return 0

    def _is_test_file(self, filepath: str) -> bool:
        """Check if file is a test file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            True if file is a test
        """
        return any(pattern in filepath for pattern in self.TEST_PATTERNS)

    def _has_dockerfile(self) -> bool:
        """Check if project has Dockerfile."""
        return (self.repo_path / "Dockerfile").exists()

    def _has_makefile(self) -> bool:
        """Check if project has Makefile."""
        return (self.repo_path / "Makefile").exists()

    def _has_ci_cd(self) -> bool:
        """Check if project has CI/CD configuration."""
        ci_paths = [
            ".github/workflows",
            ".gitlab-ci.yml",
            ".circleci",
            "azure-pipelines.yml",
        ]
        return any((self.repo_path / path).exists() for path in ci_paths)

    def _find_config_files(self) -> List[str]:
        """Find common configuration files.
        
        Returns:
            List of found config files
        """
        config_patterns = [
            "package.json",
            "requirements.txt",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            ".env",
            ".env.example",
            "config.yml",
            "config.yaml",
            ".eslintrc",
            "pytest.ini",
        ]
        
        found = []
        for pattern in config_patterns:
            if (self.repo_path / pattern).exists():
                found.append(pattern)
        
        return found
