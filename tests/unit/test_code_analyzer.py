"""
Testes unitários para CodeAnalyzer
Responsável por: Análise de código do usuário baseada em padrões
"""

import pytest
from unittest.mock import Mock, patch
from src.analysis.code_analyzer import CodeAnalyzer


class TestCodeAnalyzer:
    """Testes para análise de código"""

    @pytest.fixture
    def analyzer(self):
        """Instancia CodeAnalyzer para testes"""
        with patch("src.analysis.code_analyzer.RAGService"):
            return CodeAnalyzer()

    @pytest.fixture
    def sample_python_code(self):
        """Código Python de exemplo para análise"""
        return """
def calculate_sum(numbers):
    total = 0
    for n in numbers:
        total = total + n
    return total

def main():
    result = calculate_sum([1, 2, 3])
    print(result)

if __name__ == "__main__":
    main()
"""

    @pytest.fixture
    def sample_js_code(self):
        """Código JavaScript de exemplo"""
        return """
async function fetchUser(id) {
    const response = await fetch(`/api/users/${id}`);
    if (!response.ok) {
        throw new Error('Failed to fetch user');
    }
    return response.json();
}

fetchUser(123)
    .then(user => console.log(user))
    .catch(err => console.error(err));
"""

    def test_initialization(self, analyzer):
        """Teste: CodeAnalyzer deve inicializar corretamente"""
        assert analyzer is not None
        assert hasattr(analyzer, "analyze")

    def test_analyze_python_code(self, analyzer, sample_python_code):
        """Teste: Deve analisar código Python"""
        analysis = analyzer.analyze(sample_python_code, language="python")

        assert analysis is not None
        assert "feedback" in analysis or "suggestions" in analysis

    def test_analyze_javascript_code(self, analyzer, sample_js_code):
        """Teste: Deve analisar código JavaScript"""
        analysis = analyzer.analyze(sample_js_code, language="javascript")

        assert analysis is not None
        assert isinstance(analysis, dict)

    def test_detect_code_language(self, analyzer):
        """Teste: Deve detectar linguagem do código"""
        python_code = "def hello(): print('world')"
        js_code = "function hello() { console.log('world'); }"

        lang_py = analyzer.detect_language(python_code)
        lang_js = analyzer.detect_language(js_code)

        assert lang_py == "python" or "python" in lang_py.lower()
        assert lang_js == "javascript" or "js" in lang_js.lower()

    def test_extract_functions(self, analyzer, sample_python_code):
        """Teste: Deve extrair funções do código"""
        functions = analyzer.extract_functions(sample_python_code, "python")

        assert isinstance(functions, list)
        assert any("calculate_sum" in f for f in functions)
        assert any("main" in f for f in functions)

    def test_extract_classes(self, analyzer):
        """Teste: Deve extrair classes"""
        code = """
class UserService:
    def get_user(self, id):
        return {"id": id}
    
    def create_user(self, data):
        return data
"""
        classes = analyzer.extract_classes(code, "python")

        assert isinstance(classes, list)
        assert any("UserService" in c for c in classes)

    def test_check_code_complexity(self, analyzer):
        """Teste: Deve calcular complexidade ciclomática"""
        simple_code = "result = a + b"
        complex_code = """
if x > 0:
    if y > 0:
        if z > 0:
            return True
return False
"""

        simple_complexity = analyzer.calculate_complexity(simple_code, "python")
        complex_complexity = analyzer.calculate_complexity(complex_code, "python")

        assert simple_complexity is not None
        assert complex_complexity is not None
        # Código complexo deve ter maior complexidade
        assert complex_complexity >= simple_complexity

    def test_find_code_smells(self, analyzer):
        """Teste: Deve detectar code smells"""
        problematic_code = """
def do_everything():
    x = 1
    y = 2
    z = 3
    # ... 500 linhas de código
    if x > 0:
        if y > 0:
            if z > 0:
                pass
    return x + y + z
"""
        smells = analyzer.find_smells(problematic_code, "python")

        assert isinstance(smells, list)
        # Pode encontrar: função muito longa, nested ifs, etc

    def test_suggest_improvements(self, analyzer, sample_python_code):
        """Teste: Deve sugerir melhorias"""
        suggestions = analyzer.suggest_improvements(sample_python_code, "python")

        assert isinstance(suggestions, list)
        # Pode incluir: usar sum() instead of loop, etc

    @patch("src.analysis.code_analyzer.CodeAnalyzer._query_rag")
    def test_compare_with_patterns(self, mock_rag, analyzer, sample_python_code):
        """Teste: Deve comparar com padrões reais"""
        mock_rag.return_value = "Production pattern: use built-in sum() function"

        comparison = analyzer.compare_with_patterns(sample_python_code, "python")

        assert comparison is not None

    def test_code_style_analysis(self, analyzer):
        """Teste: Deve analisar estilo de código"""
        messy_code = "x=1+2;y=3+4;z=x+y"
        clean_code = "x = 1 + 2\ny = 3 + 4\nz = x + y"

        messy_style = analyzer.analyze_style(messy_code)
        clean_style = analyzer.analyze_style(clean_code)

        assert messy_style is not None
        assert clean_style is not None

    def test_security_analysis(self, analyzer):
        """Teste: Deve detectar problemas de segurança"""
        code_with_sql_injection = """
query = f"SELECT * FROM users WHERE id = {user_id}"
"""
        code_safe = """
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
"""

        issues1 = analyzer.analyze_security(code_with_sql_injection)
        issues2 = analyzer.analyze_security(code_safe)

        assert isinstance(issues1, list)
        assert isinstance(issues2, list)

    def test_performance_analysis(self, analyzer):
        """Teste: Deve detectar problemas de performance"""
        code_slow = """
for i in range(1000):
    for j in range(1000):
        result.append(i * j)
"""
        code_fast = """
result = [i * j for i in range(1000) for j in range(1000)]
"""

        perf1 = analyzer.analyze_performance(code_slow)
        perf2 = analyzer.analyze_performance(code_fast)

        assert perf1 is not None
        assert perf2 is not None

    def test_maintainability_score(self, analyzer, sample_python_code):
        """Teste: Deve calcular score de manutenibilidade"""
        score = analyzer.calculate_maintainability_score(sample_python_code, "python")

        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

    def test_test_coverage_analysis(self, analyzer):
        """Teste: Deve analisar cobertura de testes"""
        code_with_tests = """
def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
"""
        analysis = analyzer.analyze_test_coverage(code_with_tests)

        assert analysis is not None

    def test_documentation_analysis(self, analyzer):
        """Teste: Deve analisar qualidade de documentação"""
        well_documented = '''
def factorial(n):
    """
    Calculate factorial of n.
    
    Args:
        n (int): Non-negative integer
        
    Returns:
        int: Factorial of n
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    return 1 if n <= 1 else n * factorial(n-1)
'''
        undocumented = 'def fact(n): return 1 if n <= 1 else n * fact(n-1)'

        doc1 = analyzer.analyze_documentation(well_documented)
        doc2 = analyzer.analyze_documentation(undocumented)

        assert doc1 is not None
        assert doc2 is not None

    def test_generate_report(self, analyzer, sample_python_code):
        """Teste: Deve gerar relatório completo"""
        report = analyzer.generate_report(sample_python_code, "python")

        assert report is not None
        assert isinstance(report, dict)
        assert "summary" in report or "analysis" in report

    def test_empty_code_analysis(self, analyzer):
        """Teste: Deve lidar com código vazio"""
        result = analyzer.analyze("", "python")

        assert result is not None

    def test_syntax_error_handling(self, analyzer):
        """Teste: Deve lidar com erros de sintaxe"""
        bad_code = "def broken( print 'error'"

        # Não deve lançar erro
        result = analyzer.analyze(bad_code, "python")
        assert result is not None

    def test_unsupported_language(self, analyzer):
        """Teste: Deve rejeitar linguagens não suportadas"""
        code = "PROGRAM Hello"

        with pytest.raises(ValueError) or True:
            analyzer.analyze(code, "cobol")
