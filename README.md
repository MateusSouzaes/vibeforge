# 🧭 VibeForge

> **Forge code patterns. Elevate quality.**

VibeForge is a semi-autonomous development guidance system that absorbs proven patterns from real projects and generates high-quality roadmaps for new initiatives. It reduces technical debt **before it exists** by guiding developers from day one with battle-tested architectural patterns.

---

## 🎯 Core Mission

Transform how developers **start** projects by providing:

1. **Pattern Absorption** - Analyze repositories to extract proven architectures
2. **Pattern Recognition** - Identify and classify reusable code patterns
3. **Smart Guidance** - Generate roadmaps that prevent debt accumulation
4. **Quality Assurance** - Enforce best practices from inception

---

## 🚀 Features (Roadmap)

| Phase | Feature | Status | UC |
|-------|---------|--------|-----|
| **v1.0** | Repository Downloader | ✅ Complete | UC-001 |
| **v1.1** | Code Parser & Pattern Extraction | 🔄 In Progress | UC-002 |
| **v1.2** | Git History & Commit Analysis | ⏳ Planned | UC-003 |
| **v1.3** | Embeddings & Vector DB Integration | ⏳ Planned | UC-004 |
| **v1.4** | Query & Search Engine | ⏳ Planned | UC-005 |
| **v2.0** | 🌟 Roadmap Generation (CORE) | ⏳ Planned | UC-006 |
| **v2.1** | Live Code Analysis | ⏳ Planned | UC-007 |

---

## 📋 Quick Start

### Prerequisites

- Python 3.12+
- Git
- GitHub CLI (`gh`)
- Virtual Environment

### Installation

```bash
# Clone repository
git clone https://github.com/MateusSouzaes/vibeforge.git
cd vibeforge

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements-test.txt
```

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test module
pytest tests/unit/test_repo_downloader.py -v

# Run with coverage report
pytest --cov=src --cov-report=html
```

---

## 🏗️ Architecture

### Project Structure

```
vibeforge/
├── src/
│   ├── crawler/                 # UC-001: Repository Download
│   ├── processor/               # UC-002: Pattern Extraction (WIP)
│   ├── embeddings/              # UC-004: Vector Storage
│   ├── rag/                     # UC-005: Search & Retrieval
│   └── analysis/                # UC-006: Roadmap Generation
├── tests/
│   └── unit/                    # 124+ Target Tests (70%+ coverage)
├── scripts/
│   ├── download_repos.py        # Data collection
│   ├── extract_commits.py       # History extraction
│   └── process_files.py         # File processing
├── data/
│   ├── raw/                     # Downloaded repositories
│   ├── processed/               # Analyzed patterns
│   └── repos/                   # Analysis data
├── pytest.ini                   # Test configuration
├── requirements-test.txt        # Dependencies
└── README.md                    # This file
```

### Technology Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.12+ |
| **Framework** | FastAPI 0.110+ |
| **LLM Orchestration** | AdalFlow (PyTorch-style patterns) |
| **Vector DB** | ChromaDB 1.5.5 + FAISS |
| **LLM Provider** | Google Gemini 1.5 Flash (multi-provider fallback) |
| **Testing** | Pytest 8.0+ (target: 124 tests, 70%+ coverage) |
| **Package Manager** | pip |

### Design Patterns (SylphAI-Inspired)

1. **Component Hierarchy** - Traçability via `@component_track()`
2. **Multi-Provider LLM Fallback** - Claude → Groq → Ollama
3. **Config Layering** - default.yaml + production.yaml + .env
4. **Retriever Pattern** - Embeddings + ChromaDB search
5. **Runner Orchestration** - Step history tracking
6. **Tool Manager** - Sandboxed execution

---

## 🧪 Testing

### Coverage Target

- **Minimum:** 70% coverage
- **Target:** 124 tests across all UCs
- **Current:** 14/14 UC-001 tests passing (72% coverage)

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific marker
pytest -m unit

# Run with coverage report
pytest --cov=src --cov-report=term-missing
```

### Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── unit/
│   ├── test_repo_downloader.py (14 tests ✅)
│   ├── test_code_parser.py     (WIP)
│   ├── test_pattern_analyzer.py
│   └── ...
└── integration/                # Coming soon
```

---

## 📝 Development Workflow

### Commit Strategy

VibeForge follows **Conventional Commits v1.0.0** for clean, traceable history:

```
<type>(<scope>): <subject>

Types: feat, fix, docs, test, refactor, perf, style, chore, ci
Scopes: crawler, processor, extractor, embeddings, query, roadmap, analyzer, api, config, tests, docs

Example:
feat(processor): implement code parser for Python
test(processor): add 15 unit tests
```

### Phase-Based Development

Each UC follows a dedicated phase:

1. **Design** - Create specification
2. **Implement** - Write core functionality
3. **Test** - Add comprehensive tests
4. **Commit** - Create structured commit
5. **Document** - Update guides

---

## 🌍 Current Use Cases (UCs)

### ✅ UC-001: Repository Downloader
**Status:** Complete (v1.0)
- Download GitHub repos efficiently
- Rate limit handling (429 detection)
- Shallow clone optimization (`--depth 1`)
- Post-clone cleanup (14+ directory types)

### 🔄 UC-002: Parser & Pattern Extraction
**Status:** In Progress (v1.1)
- Parse code structure (Python, JavaScript, TypeScript, Rust, Go, Java)
- Extract dependencies
- Detect patterns
- Generate normalized JSON output

### ⏳ UC-003: Git History Analysis
- Extract commit patterns
- Analyze decision history
- Map architectural evolution

### ⏳ UC-004: Embeddings & ChromaDB
- Generate code embeddings
- Index in vector database
- FAISS optimization

### ⏳ UC-005: Query & Search Engine
- Semantic search over patterns
- Multi-provider LLM integration

### 🌟 ⏳ UC-006: Roadmap Generation (CORE)
- Analyze new project requirements
- Generate architecture roadmap
- Suggest best practices
- Prevent technical debt

### ⏳ UC-007: Live Code Analysis
- Real-time pattern detection
- Quality suggestions

---

## 📊 Metrics & Progress

```
Total Tests:        14/124 (11%)  ✅ UC-001 complete
Code Coverage:      72% / 70%     ✅ Exceeds target
Commits:            1 (a968205)   ✅ Foundation laid
UCs Complete:       1/7 (14%)
UCs In Progress:    1/7 (14%)
UCs Planned:        5/7 (71%)
```

---

## 🤝 Contributing

VibeForge is a guided development system. When contributing:

1. Follow **Conventional Commits** format
2. Aim for **70%+ test coverage**
3. Run tests before committing: `pytest`

---

## 📄 License

MIT License - See LICENSE file for details

---


```
VibeForge v1.0.0 | Repository: github.com/MateusSouzaes/vibeforge | Last Update: 2026-03-20
```
