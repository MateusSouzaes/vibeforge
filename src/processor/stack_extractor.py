"""Extract dependencies from various package managers."""

from pathlib import Path
from typing import List, Dict, Set
from src.processor.models import Dependency


class StackExtractor:
    """Extract project dependencies from various package managers."""

    def __init__(self, repo_path: str):
        """Initialize extractor.
        
        Args:
            repo_path: Path to repository
        """
        self.repo_path = Path(repo_path)

    def extract_all_dependencies(self) -> List[Dependency]:
        """Extract all dependencies from the project.
        
        Returns:
            List of all found dependencies
        """
        dependencies: List[Dependency] = []
        
        dependencies.extend(self._extract_pip())
        dependencies.extend(self._extract_npm())
        dependencies.extend(self._extract_cargo())
        dependencies.extend(self._extract_go())
        dependencies.extend(self._extract_java())
        
        # Remove duplicates by name
        seen = set()
        unique = []
        for dep in dependencies:
            if dep.name not in seen:
                seen.add(dep.name)
                unique.append(dep)
        
        return unique

    def _extract_pip(self) -> List[Dependency]:
        """Extract pip dependencies from requirements.txt or setup.py.
        
        Returns:
            List of pip dependencies
        """
        dependencies = []
        
        # Check requirements.txt
        req_file = self.repo_path / "requirements.txt"
        if req_file.exists():
            dependencies.extend(self._parse_requirements_file(req_file))
        
        # Check requirements-dev.txt
        req_dev = self.repo_path / "requirements-dev.txt"
        if req_dev.exists():
            dependencies.extend(self._parse_requirements_file(req_dev))
        
        # Check pyproject.toml (simplified parsing)
        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            dependencies.extend(self._parse_pyproject(pyproject))
        
        return dependencies

    def _extract_npm(self) -> List[Dependency]:
        """Extract npm/yarn dependencies from package.json.
        
        Returns:
            List of npm dependencies
        """
        dependencies = []
        package_json = self.repo_path / "package.json"
        
        if not package_json.exists():
            return dependencies
        
        try:
            import json
            content = json.loads(package_json.read_text())
            
            # Extract regular dependencies
            for name, version in content.get("dependencies", {}).items():
                dependencies.append(Dependency(
                    name=name,
                    version=version.lstrip("^~>=<"),
                    source="npm"
                ))
            
            # Extract dev dependencies
            for name, version in content.get("devDependencies", {}).items():
                dependencies.append(Dependency(
                    name=name,
                    version=version.lstrip("^~>=<"),
                    source="npm"
                ))
        except Exception:
            pass
        
        return dependencies

    def _extract_cargo(self) -> List[Dependency]:
        """Extract Rust dependencies from Cargo.toml.
        
        Returns:
            List of Cargo dependencies
        """
        dependencies = []
        cargo_toml = self.repo_path / "Cargo.toml"
        
        if not cargo_toml.exists():
            return dependencies
        
        try:
            content = cargo_toml.read_text()
            in_deps = False
            
            for line in content.splitlines():
                line = line.strip()
                
                if line == "[dependencies]":
                    in_deps = True
                    continue
                
                if line.startswith("[") and line != "[dependencies]":
                    in_deps = False
                
                if in_deps and "=" in line:
                    # Parse "name = "version"" or "name = { version = "..." }"
                    parts = line.split("=", 1)
                    if parts:
                        name = parts[0].strip().strip('"')
                        if name:
                            dependencies.append(Dependency(
                                name=name,
                                source="cargo"
                            ))
        except Exception:
            pass
        
        return dependencies

    def _extract_go(self) -> List[Dependency]:
        """Extract Go dependencies from go.mod.
        
        Returns:
            List of Go dependencies
        """
        dependencies = []
        go_mod = self.repo_path / "go.mod"
        
        if not go_mod.exists():
            return dependencies
        
        try:
            content = go_mod.read_text()
            in_require = False
            
            for line in content.splitlines():
                line = line.strip()
                
                if line.startswith("require"):
                    in_require = True
                    continue
                
                if line.startswith(")"):
                    in_require = False
                    continue
                
                if in_require and line and not line.startswith("//"):
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[0]
                        version = parts[1]
                        dependencies.append(Dependency(
                            name=name,
                            version=version,
                            source="go"
                        ))
        except Exception:
            pass
        
        return dependencies

    def _extract_java(self) -> List[Dependency]:
        """Extract Java dependencies from pom.xml.
        
        Returns:
            List of Maven dependencies
        """
        dependencies = []
        pom_xml = self.repo_path / "pom.xml"
        
        if not pom_xml.exists():
            return dependencies
        
        try:
            content = pom_xml.read_text()
            in_deps = False
            current_dep = {}
            
            for line in content.splitlines():
                line_stripped = line.strip()
                
                if "<dependencies>" in line:
                    in_deps = True
                
                if "</dependencies>" in line:
                    in_deps = False
                
                if in_deps:
                    if "<dependency>" in line:
                        current_dep = {}
                    
                    if "<artifactId>" in line:
                        artifact = line_stripped.replace("<artifactId>", "").replace("</artifactId>", "")
                        current_dep["name"] = artifact
                    
                    if "<version>" in line:
                        version = line_stripped.replace("<version>", "").replace("</version>", "")
                        current_dep["version"] = version
                    
                    if "</dependency>" in line and current_dep.get("name"):
                        dependencies.append(Dependency(
                            name=current_dep.get("name"),
                            version=current_dep.get("version"),
                            source="maven"
                        ))
        except Exception:
            pass
        
        return dependencies

    def _parse_requirements_file(self, filepath: Path) -> List[Dependency]:
        """Parse Python requirements file.
        
        Args:
            filepath: Path to requirements file
            
        Returns:
            List of dependencies found
        """
        dependencies = []
        
        try:
            for line in filepath.read_text().splitlines():
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                
                # Parse requirement line (simplified)
                # Handles: package==1.0, package>=1.0, package, etc
                if "==" in line:
                    name, version = line.split("==", 1)
                    dependencies.append(Dependency(
                        name=name.strip(),
                        version=version.strip(),
                        source="pip"
                    ))
                elif any(op in line for op in [">=", "<=", ">", "<", "~="]):
                    # Extract name before operator
                    for op in [">=", "<=", "~=", "!=", ">", "<", "=="]:
                        if op in line:
                            name = line.split(op)[0].strip()
                            dependencies.append(Dependency(
                                name=name,
                                source="pip"
                            ))
                            break
                else:
                    # Just a name, no version
                    dependencies.append(Dependency(
                        name=line,
                        source="pip"
                    ))
        except Exception:
            pass
        
        return dependencies

    def _parse_pyproject(self, filepath: Path) -> List[Dependency]:
        """Parse pyproject.toml for dependencies.
        
        Args:
            filepath: Path to pyproject.toml
            
        Returns:
            List of dependencies found
        """
        dependencies = []
        
        try:
            content = filepath.read_text()
            in_deps = False
            
            for line in content.splitlines():
                line_stripped = line.strip()
                
                if 'dependencies = [' in line or '[project]' in line:
                    in_deps = True
                
                if in_deps and line_stripped.startswith('"""') or line_stripped.startswith("'''"):
                    # Extract from docstring format
                    if '=' in line_stripped:
                        parts = line_stripped.split('=', 1)
                        name = parts[0].strip().strip('"').strip("'")
                        if name:
                            dependencies.append(Dependency(
                                name=name,
                                source="pip"
                            ))
        except Exception:
            pass
        
        return dependencies
