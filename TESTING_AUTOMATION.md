# 🧪 Automação de Testes - VibeForge

## Opções de Automação Disponíveis

### 1️⃣ **GitHub Actions** (Automático no GitHub)
- ✅ Roda em cada push automaticamente
- ✅ Roda em Pull Requests
- ✅ Gera relatório de cobertura
- ✅ **Sem aprovação necessária**

**Arquivo:** `.github/workflows/tests.yml`

Os testes rodam automaticamente quando você faz push! Veja em: https://github.com/MateusSouzaes/vibeforge/actions

---

### 2️⃣ **Pré-Commit Hook** (Automático antes de commit)
Roda testes locally antes de permitir commit.

**Setup (uma vez):**
```bash
# Linux/Mac
chmod +x .git/hooks/pre-commit

# Windows (PowerShell)
icacls ".git\hooks\pre-commit" /grant:r "%username%:F"
```

**Como funciona:**
```bash
git commit -m "sua mensagem"
#  → Roda testes automaticamente
#  → Se passar ✅ → Faz commit
#  → Se falhar ❌ → Aborta commit
```

**Para pular (não recomendado):**
```bash
git commit --no-verify
```

---

### 3️⃣ **VS Code - Um Clique**
Clique em um botão para rodar testes sem aprovação.

**Atalhos:**
- `Ctrl+Shift+P` → Busque "Tasks: Run Task"
- Escolha uma opção:
  - 🧪 **Run All Tests** (padrão)
  - 🧪 **Run Unit Tests Only**
  - 🧪 **Run Tests with Coverage**
  - 🚀 **Run Automated Test Suite**
  - 📊 **View Coverage Report**
  - 🔄 **Watch Tests** (auto-run em mudanças)

---

### 4️⃣ **Script Python** (Manual rápido)
```bash
python run_tests.py
```

Executa todos os testes + cobertura + relatório.

---

### 5️⃣ **Linha de Comando** (Controle total)
```bash
# Todos os testes
pytest tests/ -v

# Apenas unit tests
pytest tests/unit/ -v

# Com cobertura
pytest tests/ -v --cov=src --cov-report=html

# Específico
pytest tests/unit/test_embedding_generator.py -v

# Stop no primeiro erro
pytest tests/ -x

# Modo verbose (detalhado)
pytest tests/ -vv -s
```

---

## 🎯 Fluxo Recomendado

### Desenvolvimento Local
1. Edite código
2. Rode: `pytest tests/ -v` (rápido)
3. Se tudo funciona → `git add . && git commit -m "..."`
4. Pré-commit hook roda testes automaticamente
5. Se passou → Commit foi feito ✅
6. Faça push → GitHub Actions roda testes novamente

### Resultado
- ✅ Testes rodam 3x (local + pre-commit + GitHub)
- ✅ Nenhuma aprovação manual necessária
- ✅ Histórico de testes no GitHub

---

## 📊 Visualizar Resultados

### Coverage Report (local)
```bash
pytest tests/ --cov=src --cov-report=html
# Abre: htmlcov/index.html
```

### GitHub
- Vá para: https://github.com/MateusSouzaes/vibeforge/actions
- Veja cada execução de teste e resultado

### Codecov (opcional)
Integração automática via GitHub Actions (já configurada)

---

## ⚙️ Configuração Customizada

### Adicionar mais testes automaticamente
1. Crie arquivo `tests/unit/test_*.py`
2. GitHub Actions detecta automaticamente
3. Roda em próximo push

### Mudar branches que rodam testes
**Arquivo:** `.github/workflows/tests.yml`
```yaml
on:
  push:
    branches: [ master, main, develop ]  # ← Customize aqui
```

### Desabilitar pré-commit
```bash
# Windows
del .git\hooks\pre-commit

# Linux/Mac
rm .git/hooks/pre-commit
```

---

## 🚀 Próximos Passos

1. **Commit** as mudanças de automação:
```bash
git add .github/ .vscode/ requirements.txt run_tests.py
git commit -m "feat: setup automated testing with GitHub Actions"
git push
```

2. **Veja** os testes rodando automaticamente:
- Vá para GitHub → Actions
- Selecione o último push
- Veja os testes executando em tempo real

3. **Customize** conforme necessário

---

## 💡 Dicas

- **Testes rápidos:** `pytest tests/unit/test_embedding_generator.py -v`
- **Debug:** `pytest tests/ -v -s` (mostra prints)
- **Específico:** `pytest tests/ -k "test_search" -v` (só tests com "search")
- **Paralelo:** `pytest tests/ -n auto` (roda múltiplos cores)

---

## ❓ Troubleshooting

**"Pré-commit não roda"**
- Certifique-se que `.git/hooks/pre-commit` existe e tem permissão de execução
- Windows: `icacls ".git\hooks\pre-commit" /grant:r "%username%:F"`

**"GitHub Actions não roda"**
- Vá para: https://github.com/MateusSouzaes/vibeforge/settings/actions
- Certifique que Actions está habilitado
- Cheque se arquivo `.github/workflows/tests.yml` existe

**"Testes locais passam mas GitHub falha"**
- Provavelmente versão Python diferente
- Verifica em `.github/workflows/tests.yml` qual versão roda lá
- Iguale sua versão local
