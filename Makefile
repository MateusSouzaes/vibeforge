.PHONY: help test test-unit test-integration test-coverage test-fast clean install-test lint

help:
	@echo "🧪 Sistema de Engenheiro Digital - Comandos de Teste"
	@echo ""
	@echo "Uso: make [comando]"
	@echo ""
	@echo "Comandos disponíveis:"
	@echo "  make test               - Executar todos os testes"
	@echo "  make test-unit          - Executar apenas testes unitários"
	@echo "  make test-integration   - Executar apenas testes de integração"
	@echo "  make test-coverage      - Executar testes com cobertura"
	@echo "  make test-fast          - Executar testes rápidos"
	@echo "  make test-debug         - Executar com debugger"
	@echo "  make test-watch         - Executar testes em watch mode"
	@echo "  make install-test       - Instalar dependências de teste"
	@echo "  make lint               - Executar linting"
	@echo "  make format             - Formatar código"
	@echo "  make clean              - Limpar arquivos de teste"
	@echo ""

# Instalar dependências
install-test:
	pip install -r requirements-test.txt

# Testes básicos
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v -m unit

test-integration:
	pytest tests/integration/ -v -m integration

# Testes com cobertura
test-coverage:
	pytest tests/ \
		--cov=src \
		--cov-report=html \
		--cov-report=term-missing \
		--cov-fail-under=70 \
		-v
	@echo ""
	@echo "✅ Relatório de cobertura gerado em: htmlcov/index.html"

# Testes rápidos (sem API)
test-fast:
	pytest tests/unit/ -v -m "not requires_api" --tb=short

# Testes com debugger
test-debug:
	pytest tests/ -vv --pdb --tb=short

# Testes em watch mode
test-watch:
	pytest-watch tests/unit/ -v

# Linting
lint:
	@echo "🔍 Executando linting..."
	flake8 src tests --max-line-length=100 --exclude=__pycache__
	pylint src --disable=R,C
	black --check src tests
	isort --check-only src tests

# Formatação automática
format:
	@echo "🎨 Formatando código..."
	black src tests
	isort src tests

# Limpeza
clean:
	@echo "🧹 Limpando arquivos de teste..."
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf *.pyc
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Limpeza concluída"

# Teste específico
test-one:
	@echo "Digite o caminho do teste (ex: tests/unit/test_repo_downloader.py::TestRepoDownloader::test_initialization):"
	@read test_path; pytest $$test_path -v

# Correlação entre testes
test-correlation:
	pytest tests/ \
		--cov=src \
		--cov-report=term-missing \
		--html=report.html \
		--self-contained-html \
		-v

# Verificação pré-commit
pre-commit: format lint test-fast
	@echo ""
	@echo "✅ Pre-commit check passou!"

# Statistics
stats:
	@echo "📊 Estatísticas de Testes"
	@echo ""
	@find tests/unit -name "test_*.py" -exec wc -l {} +
	@echo ""
	@echo "Total de linhas de teste:"
	@find tests/unit -name "test_*.py" | xargs wc -l | tail -1
	@echo ""
	@echo "Total de casos de teste:"
	@grep -r "def test_" tests/unit --count

# Relatório detalhado
report: test-coverage
	@echo ""
	@echo "📈 Relatórios gerados:"
	@echo "  - HTML: htmlcov/index.html"
	@echo "  - Terminal: Veja acima"
