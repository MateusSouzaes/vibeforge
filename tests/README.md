# 🧪 Testes Unitários - Sistema de Engenheiro Digital

Bateria completa de testes unitários para o sistema de IA especializada em padrões de engenharia.

---

## 📋 Estrutura de Testes

```
tests/
├── unit/                      # Testes unitários
│   ├── test_repo_downloader.py        # Testes de ingestão GitHub
│   ├── test_commit_extractor.py       # Testes de extração de commits
│   ├── test_file_processor.py         # Testes de processamento de arquivos
│   ├── test_commit_processor.py       # Testes de processamento de commits
│   ├── test_embedding_service.py      # Testes de embeddings Gemini
│   ├── test_vector_db.py              # Testes de banco vetorial ChromaDB
│   ├── test_rag_service.py            # Testes de consulta RAG
│   └── test_code_analyzer.py          # Testes de análise de código
├── integration/               # Testes de integração (futuro)
├── conftest.py               # Configurações compartilhadas
└── README.md                 # Este arquivo
```

---

## 🚀 Instalação

### 1. Criar ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 2. Instalar dependências de teste

```bash
pip install -r requirements-test.txt
```

### 3. Configurar variáveis de ambiente

```bash
cp .env.example .env.test
# Editar .env.test com suas credenciais Gemini
```

---

## 📝 Executar Testes

### Todos os testes
```bash
pytest
```

### Apenas testes unitários
```bash
pytest tests/unit/
```

### Teste específico
```bash
pytest tests/unit/test_repo_downloader.py
pytest tests/unit/test_repo_downloader.py::TestRepoDownloader::test_initialization
```

### Com cobertura de código
```bash
pytest --cov=src --cov-report=html
# Abrir: htmlcov/index.html
```

### Com output verboso
```bash
pytest -v
pytest -vv  # Extra verboso
```

### Apenas testes rápidos
```bash
pytest -m "not slow"
```

### Apenas testes que necessitam API
```bash
pytest -m "requires_api"
```

---

## 🧪 Testes Criados

### 1. `test_repo_downloader.py`
**Responsável por:** Ingestão de repositórios GitHub

**Casos de teste:**
- ✅ Inicialização do RepoDownloader
- ✅ Busca de repositórios do usuário (sucesso)
- ✅ Tratamento de erro da API GitHub
- ✅ Clone de repositório (sucesso)
- ✅ Falha no clone
- ✅ Validação de URLs GitHub
- ✅ Fluxo completo de download
- ✅ Extração de nome do repositório

**Total:** 8 testes

---

### 2. `test_commit_extractor.py`
**Responsável por:** Extração de commits

**Casos de teste:**
- ✅ Inicialização do CommitExtractor
- ✅ Extração de commits com sucesso
- ✅ Repositório vazio
- ✅ Erro no git log
- ✅ Parse de linha de commit
- ✅ Parse de commit com mensagem longa
- ✅ Rejeição de linha inválida
- ✅ Filtro por autor
- ✅ Filtro por intervalo de datas
- ✅ Validação de hash de commit
- ✅ Rejeição de hash inválido
- ✅ Obtenção de diff do commit

**Total:** 12 testes

---

### 3. `test_file_processor.py`
**Responsável por:** Processamento de arquivos de código

**Casos de teste:**
- ✅ Inicialização do FileProcessor
- ✅ Extensões suportadas
- ✅ Validação de extensão (válida)
- ✅ Validação de extensão (inválida)
- ✅ Leitura de arquivo
- ✅ Tratamento de arquivo não encontrado
- ✅ Processamento de arquivo Python
- ✅ Criação de chunks com tamanho válido
- ✅ Preservação de contexto em chunks
- ✅ Extração de funções
- ✅ Extração de classes
- ✅ Detecção de linguagem
- ✅ Ignorar padrões de diretórios
- ✅ Processamento de diretório inteiro
- ✅ Extração de metadata do arquivo

**Total:** 15 testes

---

### 4. `test_commit_processor.py`
**Responsável por:** Processamento de commits

**Casos de teste:**
- ✅ Inicialização do CommitProcessor
- ✅ Processamento de commits válidos
- ✅ Extração de tipo de commit
- ✅ Extração de escopo
- ✅ Normalização de mensagem
- ✅ Enriquecimento de commits
- ✅ Extração de domínio do email
- ✅ Extração de keywords
- ✅ Agrupamento por tipo
- ✅ Agrupamento por autor
- ✅ Cálculo de estatísticas
- ✅ Detecção de merge commits
- ✅ Identificação de commits normais
- ✅ Filtro por intervalo de datas
- ✅ Filtro por autor
- ✅ Tratamento de campos faltando

**Total:** 16 testes

---

### 5. `test_embedding_service.py`
**Responsável por:** Geração de embeddings com Gemini

**Casos de teste:**
- ✅ Inicialização do EmbeddingService
- ✅ Uso de API key do ambiente
- ✅ Geração de embedding (sucesso)
- ✅ Tratamento de erro da API
- ✅ Rejeição de texto vazio
- ✅ Validação de tamanho de texto
- ✅ Processamento em batch
- ✅ Respeitar batch_size
- ✅ Normalização de embedding
- ✅ Cálculo de similaridade do cosseno (idêntico)
- ✅ Cálculo de similaridade (ortogonal)
- ✅ Cálculo de similaridade (oposto)
- ✅ Cache de embeddings
- ✅ Limpeza de cache
- ✅ Informações do modelo
- ✅ Consistência de dimensões
- ✅ Propriedades matemáticas

**Total:** 17 testes

---

### 6. `test_vector_db.py`
**Responsável por:** Banco vetorial ChromaDB

**Casos de teste:**
- ✅ Inicialização do VectorDB
- ✅ Adicionar documento único
- ✅ Adicionar múltiplos documentos
- ✅ Busca por similaridade
- ✅ Filtro de resultados por metadata
- ✅ Recuperar documento por ID
- ✅ Retornar None para documento inexistente
- ✅ Atualizar documento
- ✅ Deletar documento
- ✅ Deletar documento inexistente
- ✅ Contar documentos na coleção
- ✅ Listar todos os documentos
- ✅ Deletar múltiplos documentos
- ✅ Limpar coleção inteira
- ✅ Ranking de resultados por relevância
- ✅ Persistência de dados
- ✅ Filtro com múltiplas condições
- ✅ Query em DB vazio

**Total:** 18 testes

---

### 7. `test_rag_service.py`
**Responsável por:** Consultas RAG

**Casos de teste:**
- ✅ Inicialização do RAGService
- ✅ Adicionar documento único
- ✅ Adicionar múltiplos documentos
- ✅ Query com sucesso
- ✅ Recuperar documentos de contexto
- ✅ Gerar resposta com contexto
- ✅ Rejeição de query vazia
- ✅ Validação de comprimento de query
- ✅ Respeitar janela de contexto
- ✅ Suporte a filtros
- ✅ Montagem de prompt
- ✅ Incluir todos os documentos no prompt
- ✅ Parse de metadata da resposta
- ✅ Lidar com falta de contexto
- ✅ Scoring de similaridade
- ✅ Limpeza do banco RAG
- ✅ Estatísticas do RAG
- ✅ Cache de respostas

**Total:** 18 testes

---

### 8. `test_code_analyzer.py`
**Responsável por:** Análise de código

**Casos de teste:**
- ✅ Inicialização do CodeAnalyzer
- ✅ Análise de código Python
- ✅ Análise de código JavaScript
- ✅ Detecção de linguagem
- ✅ Extração de funções
- ✅ Extração de classes
- ✅ Cálculo de complexidade ciclomática
- ✅ Detecção de code smells
- ✅ Sugestões de melhoria
- ✅ Comparação com padrões reais
- ✅ Análise de estilo de código
- ✅ Análise de segurança
- ✅ Análise de performance
- ✅ Score de manutenibilidade
- ✅ Análise de cobertura de testes
- ✅ Análise de documentação
- ✅ Geração de relatório completo
- ✅ Tratamento de código vazio
- ✅ Tratamento de erros de sintaxe
- ✅ Rejeição de linguagem não suportada

**Total:** 20 testes

---

## 📊 Resumo de Cobertura

| Módulo | Testes | Cobertura Esperada |
|--------|--------|-------------------|
| `repo_downloader.py` | 8 | 85%+ |
| `commit_extractor.py` | 12 | 85%+ |
| `file_processor.py` | 15 | 80%+ |
| `commit_processor.py` | 16 | 85%+ |
| `embedding_service.py` | 17 | 85%+ |
| `vector_db.py` | 18 | 85%+ |
| `rag_service.py` | 18 | 80%+ |
| `code_analyzer.py` | 20 | 80%+ |
| **TOTAL** | **124** | **83%+** |

---

## 🔍 Padrões de Teste Utilizados

### 1. Arrange-Act-Assert
```python
def test_example(self):
    # Arrange
    input_data = ...
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_value
```

### 2. Mocking de Dependências
```python
@patch("module.external_api")
def test_with_mock(mock_api):
    mock_api.return_value = expected_response
    result = function_under_test()
    assert result is not None
```

### 3. Fixtures
```python
@pytest.fixture
def sample_data():
    return {"id": 1, "name": "test"}
```

### 4. Parametrização
```python
@pytest.mark.parametrize("input,expected", [
    ("a", 1),
    ("b", 2),
])
def test_function(input, expected):
    assert function(input) == expected
```

---

## 📈 Executar com Relatório

### Gerar HTML Report
```bash
pytest --html=report.html --self-contained-html
```

### Gerar JSON Report
```bash
pytest --json-report --json-report-file=report.json
```

### Acompanhar Progresso
```bash
pytest -v --tb=short --color=yes
```

---

## 🐛 Debugging

### Parar no primeiro erro
```bash
pytest -x
```

### Parar após N erros
```bash
pytest --maxfail=3
```

### Last failed
```bash
pytest --lf
```

### Print statements ativado
```bash
pytest -s
```

### PDB (debugger) em falhas
```bash
pytest --pdb
```

---

## ✅ Validação antes de Commit

```bash
# Executar testes + linting
make test

# Ou manualmente:
pytest
black src tests
isort src tests
flake8 src tests
```

---

## 📚 Referências

- [Pytest Documentation](https://docs.pytest.org/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://testingpython.com/)

---

**Total de Testes Criados: 124** ✅
