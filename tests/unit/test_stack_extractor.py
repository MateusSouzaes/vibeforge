"""Tests for stack extractor module."""

import pytest
import tempfile
import json
from pathlib import Path
from src.processor.stack_extractor import StackExtractor


@pytest.fixture
def project_with_pip():
    """Create project with pip dependencies."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create requirements.txt
        (tmp_path / "requirements.txt").write_text(
            "pytest==8.0.0\n"
            "requests>=2.30.0\n"
            "flask\n"
        )
        
        yield tmp_path


@pytest.fixture
def project_with_npm():
    """Create project with npm dependencies."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create package.json
        package = {
            "dependencies": {
                "express": "^4.18.0",
                "axios": "~1.6.0"
            },
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package))
        
        yield tmp_path


@pytest.fixture
def project_with_cargo():
    """Create project with Cargo dependencies."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create Cargo.toml
        (tmp_path / "Cargo.toml").write_text("""
[package]
name = "my-project"
version = "0.1.0"

[dependencies]
tokio = "1.35"
serde = { version = "1.0", features = ["derive"] }
""")
        
        yield tmp_path


@pytest.fixture
def project_with_go():
    """Create project with Go dependencies."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create go.mod
        (tmp_path / "go.mod").write_text("""
module github.com/example/myapp

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/lib/pq v1.10.9
)
""")
        
        yield tmp_path


@pytest.fixture
def project_with_maven():
    """Create project with Maven dependencies."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create pom.xml
        (tmp_path / "pom.xml").write_text("""
<project>
    <dependencies>
        <dependency>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
        </dependency>
        <dependency>
            <artifactId>spring-core</artifactId>
            <version>6.0.0</version>
        </dependency>
    </dependencies>
</project>
""")
        
        yield tmp_path


class TestStackExtractor:
    """Test suite for StackExtractor."""

    def test_extract_pip_dependencies(self, project_with_pip):
        """Test pip dependency extraction."""
        extractor = StackExtractor(str(project_with_pip))
        deps = extractor._extract_pip()
        
        assert len(deps) >= 3
        names = [d.name for d in deps]
        assert "pytest" in names
        assert "requests" in names
        assert "flask" in names
        
        # Check versions
        pytest_dep = next(d for d in deps if d.name == "pytest")
        assert pytest_dep.version == "8.0.0"

    def test_extract_npm_dependencies(self, project_with_npm):
        """Test npm dependency extraction."""
        extractor = StackExtractor(str(project_with_npm))
        deps = extractor._extract_npm()
        
        assert len(deps) >= 3
        names = [d.name for d in deps]
        assert "express" in names
        assert "axios" in names
        assert "jest" in names
        
        # Check source
        assert all(d.source == "npm" for d in deps)

    def test_extract_cargo_dependencies(self, project_with_cargo):
        """Test Cargo dependency extraction."""
        extractor = StackExtractor(str(project_with_cargo))
        deps = extractor._extract_cargo()
        
        assert len(deps) >= 2
        names = [d.name for d in deps]
        assert "tokio" in names
        assert "serde" in names
        
        # Check source
        assert all(d.source == "cargo" for d in deps)

    def test_extract_go_dependencies(self, project_with_go):
        """Test Go dependency extraction."""
        extractor = StackExtractor(str(project_with_go))
        deps = extractor._extract_go()
        
        assert len(deps) >= 2
        names = [d.name for d in deps]
        assert any("gin" in name for name in names)
        assert any("pq" in name for name in names)

    def test_extract_maven_dependencies(self, project_with_maven):
        """Test Maven dependency extraction."""
        extractor = StackExtractor(str(project_with_maven))
        deps = extractor._extract_java()
        
        assert len(deps) >= 2
        names = [d.name for d in deps]
        assert "junit" in names
        assert "spring-core" in names

    def test_extract_all_dependencies(self, project_with_pip):
        """Test extracting all dependencies from project."""
        extractor = StackExtractor(str(project_with_pip))
        all_deps = extractor.extract_all_dependencies()
        
        assert len(all_deps) > 0
        assert all(d.name for d in all_deps)

    def test_removes_duplicate_dependencies(self):
        """Test that extract_all_dependencies removes duplicates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create requirements.txt and package.json with pytest
            (tmp_path / "requirements.txt").write_text("pytest==8.0.0\n")
            
            package = {
                "devDependencies": {
                    "pytest-plugin": "^1.0.0"
                }
            }
            (tmp_path / "package.json").write_text(json.dumps(package))
            
            extractor = StackExtractor(str(tmp_path))
            all_deps = extractor.extract_all_dependencies()
            
            # Should not have duplicates when combining all sources
            names = [d.name for d in all_deps]
            assert len(names) == len(set(names))

    def test_parse_requirements_with_operators(self):
        """Test parsing requirements with version operators."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            (tmp_path / "requirements.txt").write_text(
                "numpy>=1.20.0\n"
                "pandas<2.0.0\n"
                "scipy~=1.8.0\n"
            )
            
            extractor = StackExtractor(str(tmp_path))
            deps = extractor._extract_pip()
            
            names = [d.name for d in deps]
            assert "numpy" in names
            assert "pandas" in names
            assert "scipy" in names

    def test_empty_project(self):
        """Test extraction on project with no dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = StackExtractor(str(tmpdir))
            deps = extractor.extract_all_dependencies()
            
            assert deps == []

    def test_invalid_file_handling(self):
        """Test graceful handling of invalid files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create invalid JSON package.json
            (tmp_path / "package.json").write_text("invalid json {]")
            
            extractor = StackExtractor(str(tmp_path))
            deps = extractor._extract_npm()
            
            # Should return empty list without crashing
            assert deps == []
