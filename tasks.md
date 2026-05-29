# 📋 Tasks — Sprint Tracker

> **Project:** Threat Intelligence RAG Chatbot
> **Last Updated:** 2026-05-29

---

## Sprint 1 — Project Foundation `IN PROGRESS`

**Sprint Goal:** Establish a clean, professional, GitHub-ready repository.
**Duration:** 2026-05-29 → 2026-06-11

### Tasks

- [x] **TASK-001** — Initialize Git repository
  - Create repo, set default branch to `main`
  - Priority: 🔴 Critical

- [x] **TASK-002** — Define folder structure
  - Create `src/`, `tests/`, `data/`, `docs/`, `scripts/` directories
  - Create Python package `__init__.py` files
  - Priority: 🔴 Critical

- [x] **TASK-003** — Create `requirements.txt`
  - Pin all dependency versions
  - Include dev dependencies (testing, linting, formatting)
  - Priority: 🔴 Critical

- [x] **TASK-004** — Create `.gitignore`
  - Cover Python, IDE, OS, secrets, vector store, logs
  - Priority: 🔴 Critical

- [x] **TASK-005** — Create `.env.example`
  - Document all environment variables with placeholder values
  - Priority: 🟡 Medium

- [x] **TASK-006** — Write `README.md`
  - Project overview, architecture diagram, quick-start guide
  - Project structure reference, contribution guidelines
  - Priority: 🔴 Critical

- [x] **TASK-007** — Set up `docs/` folder
  - Create `docs/assets/`, `docs/api/`, `docs/guides/`
  - Create `architecture.md` skeleton
  - Create `changelog.md`
  - Priority: 🟡 Medium

- [x] **TASK-008** — Write `roadmap.md`
  - Define 6 sprints with deliverables
  - Include backlog items
  - Priority: 🟡 Medium

- [x] **TASK-009** — Write `tasks.md` (this file)
  - Sprint tracking with task IDs and priorities
  - Priority: 🟡 Medium

- [x] **TASK-010** — Write `ai_context.md`
  - Project context document for AI pair-programming
  - Tech stack, conventions, constraints
  - Priority: 🟢 Low

- [ ] **TASK-011** — Initial Git commit & push
  - Stage all Sprint 1 files, commit, push to remote
  - Priority: 🔴 Critical

---

## Sprint 2 — Core RAG Pipeline `UPCOMING`

**Sprint Goal:** Build the ingestion-to-retrieval pipeline.
**Duration:** TBD

### Tasks

- [ ] **TASK-012** — Implement `src/core/config.py`
  - Load settings from `.env` using `pydantic-settings`
  - Validate all required environment variables
  - Priority: 🔴 Critical

- [ ] **TASK-013** — Implement document loaders
  - Support PDF, DOCX, TXT, HTML formats
  - Standardized output schema per loader
  - Priority: 🔴 Critical

- [ ] **TASK-014** — Implement text chunking
  - Recursive character text splitter
  - Configurable chunk size & overlap
  - Priority: 🔴 Critical

- [ ] **TASK-015** — Integrate ChromaDB
  - Persistent vector store with configurable collection
  - Add / query / delete operations
  - Priority: 🔴 Critical

- [ ] **TASK-016** — Build embedding pipeline
  - OpenAI embeddings as default
  - Pluggable embedding model interface
  - Priority: 🔴 Critical

- [ ] **TASK-017** — Build basic retrieval chain
  - Query → embed → retrieve → prompt → LLM → response
  - Priority: 🔴 Critical

- [ ] **TASK-018** — Write unit tests
  - Test loaders, chunker, vector store, retrieval
  - Minimum 80% coverage on new code
  - Priority: 🟡 Medium

---

## Completed Sprints

_None yet — Sprint 1 in progress._

---

> **Legend:**
> 🔴 Critical · 🟡 Medium · 🟢 Low
> ✅ Done · 🔄 In Progress · 🔜 Planned
