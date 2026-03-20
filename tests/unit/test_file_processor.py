"""
Testes unitários para FileProcessor
Responsável por: Processamento de arquivos de código
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.processor.file_processor import FileProcessor


class TestFileProcessor:
    """Testes para processamento de arquivos de código"""

    @pytest.fixture
    def processor(self):
        """Instancia FileProcessor para testes"""
        return FileProcessor()

    @pytest.fixture
    def sample_code_file(self, tmp_path):
        """Cria arquivo de código de exemplo"""
        file_path = tmp_path / "example.py"
        file_path.write_text("""
def hello_world():
    '''Print hello world'''
    print("Hello, World!")

def add(a, b):
    '''Add two numbers'''
    return a + b

class MyClass:
    def method(self):
        pass
""")
        return file_path

    def test_initialization(self, processor):
        """Teste: FileProcessor deve inicializar corretamente"""
        assert processor is not None
        assert hasattr(processor, "process_file")
        assert hasattr(processor, "process_directory")

    def test_get_supported_extensions(self, processor):
        """Teste: Deve retornar list de extensões suportadas"""
        extensions = processor.get_supported_extensions()

        assert isinstance(extensions, list)
        assert ".py" in extensions
        assert ".js" in extensions
        assert ".ts" in extensions

    def test_is_supported_extension_valid(self, processor):
        """Teste: Deve identificar extensões suportadas"""
        valid_extensions = [".py", ".js", ".ts", ".java", ".go", ".rs"]

        for ext in valid_extensions:
            assert processor.is_supported_extension(ext) is True

    def test_is_supported_extension_invalid(self, processor):
        """Teste: Deve rejeitar extensões não suportadas"""
        invalid_extensions = [".txt", ".doc", ".pdf", ".exe", ""]

        for ext in invalid_extensions:
            assert processor.is_supported_extension(ext) is False

    def test_read_file_success(self, processor, sample_code_file):
        """Teste: Deve ler arquivo com sucesso"""
        content = processor.read_file(str(sample_code_file))

        assert content is not None
        assert "def hello_world" in content
        assert "def add" in content

    def test_read_file_not_found(self, processor):
        """Teste: Deve lançar erro se arquivo não existe"""
        with pytest.raises(FileNotFoundError):
            processor.read_file("/nonexistent/file.py")

    def test_process_file_python(self, processor, sample_code_file):
        """Teste: Deve processar arquivo Python"""
        result = processor.process_file(str(sample_code_file))

        assert result is not None
        assert "chunks" in result
        assert len(result["chunks"]) > 0
        assert result["file_path"] == str(sample_code_file)
        assert result["language"] == "python"

    def test_create_chunks_valid_size(self, processor, sample_code_file):
        """Teste: Deve criar chunks com tamanho válido"""
        content = processor.read_file(str(sample_code_file))
        chunks = processor.create_chunks(content, chunk_size=100, overlap=10)

        assert isinstance(chunks, list)
        assert len(chunks) > 0

        for chunk in chunks:
            assert len(chunk) <= 110  # chunk_size + overlap

    def test_create_chunks_preserves_context(self, processor):
        """Teste: Chunks devem preservar contexto com overlap"""
        content = "line 1\nline 2\nline 3\nline 4\nline 5\n"
        chunks = processor.create_chunks(content, chunk_size=20, overlap=5)

        assert len(chunks) > 0

        # Verificar que há sobreposição entre chunks
        for i in range(len(chunks) - 1):
            # O último caractere do chunk i deve estar no chunk i+1
            assert chunks[i][-5:] in chunks[i + 1]

    def test_extract_functions_from_python(self, processor, sample_code_file):
        """Teste: Deve extrair funções de arquivo Python"""
        content = processor.read_file(str(sample_code_file))
        functions = processor.extract_functions(content, "python")

        assert isinstance(functions, list)
        assert any("hello_world" in f for f in functions)
        assert any("add" in f for f in functions)

    def test_extract_classes_from_python(self, processor, sample_code_file):
        """Teste: Deve extrair classes de arquivo Python"""
        content = processor.read_file(str(sample_code_file))
        classes = processor.extract_classes(content, "python")

        assert isinstance(classes, list)
        assert any("MyClass" in c for c in classes)

    def test_detect_language_by_extension(self, processor):
        """Teste: Deve detectar linguagem pelo arquivo"""
        test_cases = [
            ("file.py", "python"),
            ("file.js", "javascript"),
            ("file.ts", "typescript"),
            ("file.java", "java"),
            ("file.go", "golang"),
            ("file.rs", "rust"),
        ]

        for filename, expected_lang in test_cases:
            lang = processor.detect_language(filename)
            assert lang == expected_lang

    def test_ignore_patterns(self, processor, tmp_path):
        """Teste: Deve ignorar diretórios e padrões"""
        # Criar estrutura de diretórios
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('main')")

        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "package.py").write_text("print('package')")

        __pycache__ = tmp_path / "__pycache__"
        __pycache__.mkdir()
        (__pycache__ / "cache.py").write_text("print('cache')")

        files = processor.list_valid_files(str(tmp_path))

        # Deve incluir main.py
        assert any("main.py" in f for f in files)

        # Deve ignorar node_modules e __pycache__
        assert not any("node_modules" in f for f in files)
        assert not any("__pycache__" in f for f in files)

    def test_process_directory(self, processor, tmp_path):
        """Teste: Deve processar diretório inteiro"""
        # Criar estrutura
        (tmp_path / "file1.py").write_text("def test(): pass")
        (tmp_path / "file2.py").write_text("class Test: pass")

        results = processor.process_directory(str(tmp_path))

        assert isinstance(results, list)
        assert len(results) >= 2

    def test_get_file_metadata(self, processor, sample_code_file):
        """Teste: Deve extrair metadata do arquivo"""
        metadata = processor.get_file_metadata(str(sample_code_file))

        assert metadata["path"] == str(sample_code_file)
        assert metadata["language"] == "python"
        assert metadata["size"] > 0
        assert "modified" in metadata
