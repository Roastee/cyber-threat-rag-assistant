# 🤖 AI Context — Threat Intelligence RAG Chatbot

> **Purpose:** This document provides context for AI coding assistants
> (Copilot, Gemini, ChatGPT, Claude, etc.) to understand the project's
> architecture, conventions, and constraints. Keep this file updated as
> the project evolves.

---

## 1. Project Overview

**Name:** Threat Intelligence RAG Chatbot
**Type:** Python backend application with REST API
**Domain:** Cybersecurity / Threat Intelligence
**Architecture:** RAG (Retrieval-Augmented Generation) pipeline

**What it does:**
- Ingests cybersecurity documents (CVE reports, MITRE ATT&CK data, OSINT feeds, internal security docs)
- Chunks, embeds, and indexes documents into a vector store
- Answers user queries by retrieving relevant context and generating grounded responses via an LLM
- Cites sources and provides confidence scores

**What it does NOT do:**
- It is NOT a general-purpose chatbot — all answers must be grounded in indexed documents
- It does NOT perform active threat hunting or scanning
- It does NOT replace a SIEM or SOAR platform

---

## 2. Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Language | Python | ≥ 3.10 |
| Web Framework | FastAPI | 0.115.x |
| LLM Orchestration | LangChain | 0.3.x |
| LLM Provider | OpenAI (GPT-4) | 1.82.x |
| Vector Store | ChromaDB | 1.0.x |
| Data Validation | Pydantic | 2.11.x |
| Testing | pytest | 8.3.x |
| Linting | ruff, black, mypy | latest |
| Logging | loguru | 0.7.x |

---

## 3. Project Structure

```
src/
├── api/          → FastAPI routes, middleware, dependencies
├── core/         → Config, settings, constants, exceptions
├── ingestion/    → Document loaders, text chunking, preprocessing
├── rag/          → Retrieval chain, prompt templates, LLM interaction
├── models/       → Pydantic schemas (request/response models)
└── utils/        → Shared helpers (logging, file I/O, text processing)

tests/
├── unit/         → Isolated unit tests per module
└── integration/  → End-to-end pipeline tests

data/
├── raw/          → Original documents (feeds/, reports/)
└── processed/    → Chunked & cleaned documents

docs/             → Architecture docs, API reference, guides
scripts/          → Utility & automation scripts
```

---

## 4. Coding Conventions

### Style
- **Formatter:** Black (line length 88)
- **Linter:** Ruff (replaces flake8 + isort)
- **Type Checker:** mypy (strict mode)
- **Docstrings:** Google style

### Naming
- **Files / modules:** `snake_case.py`
- **Classes:** `PascalCase`
- **Functions / variables:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private members:** `_leading_underscore`

### Imports
```python
# Standard library
import os
from pathlib import Path

# Third-party
from fastapi import FastAPI
from langchain.chains import RetrievalQA

# Local
from src.core.config import settings
from src.models.schemas import ChatRequest
```

### Error Handling
- Use custom exception classes defined in `src/core/exceptions.py`
- Never catch bare `except:` — always specify the exception type
- Log errors with `loguru` before re-raising

### Configuration
- All config via environment variables loaded through `pydantic-settings`
- No hardcoded secrets, API keys, or file paths
- Use `.env.example` as the reference for all variables

---

## 5. Key Design Decisions

1. **LangChain as orchestrator** — Provides abstractions for chains, retrievers, and prompt templates. Allows swapping LLM providers without rewriting pipeline logic.

2. **ChromaDB as vector store** — Lightweight, embeddable, no external server needed for development. Can migrate to Pinecone/Weaviate later.

3. **FastAPI for API layer** — Async-native, auto-generated OpenAPI docs, Pydantic integration.

4. **Modular package structure** — Each `src/` sub-package is independently testable. Clear separation between ingestion, retrieval, and API layers.

5. **Pinned dependencies** — All versions in `requirements.txt` are pinned for reproducibility. Update deliberately, not accidentally.

---

## 6. Constraints & Guardrails

- **No RAG implementation in Sprint 1** — Sprint 1 is project scaffolding only
- **All responses must cite sources** — No unsourced LLM generation
- **No PII in indexed documents** — Threat intel data only
- **API keys must never be committed** — Use `.env` + `.gitignore`
- **Tests required for all new modules** — Minimum 80% coverage target
- **Python ≥ 3.10 required** — We use modern syntax (match statements, type unions with `|`)

---

## 7. Common Commands

```bash
# Run dev server
uvicorn src.api.main:app --reload

# Run tests
pytest -v --cov=src

# Lint & format
ruff check src/ tests/
black src/ tests/
mypy src/

# Install dependencies
pip install -r requirements.txt
```

---

## 8. Current Sprint

**Sprint 1 — Project Foundation**
- Setting up repository structure, documentation, and tooling
- No functional code yet
- Next sprint: Core RAG pipeline (document ingestion + retrieval)

---

> **Maintainer:** Update this file whenever you add new modules,
> change conventions, or make architectural decisions.
