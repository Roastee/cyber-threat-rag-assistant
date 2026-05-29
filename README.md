# 🛡️ Cyber Threat RAG Assistant

> AI-powered Threat Intelligence chatbot using Retrieval-Augmented Generation (RAG) — grounded in your own security documents.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.45-FF4B4B?logo=streamlit&logoColor=white)
![Version](https://img.shields.io/badge/Version-0.4.0-00FF88)
![Status](https://img.shields.io/badge/Status-In%20Development-F59E0B)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## What Is This?

A cybersecurity-focused RAG chatbot that lets analysts upload threat intelligence PDFs, automatically processes and embeds them, and (in upcoming sprints) answers questions grounded in those documents with source citations.

**Current capabilities:**
- 📄 Upload PDFs → auto-extract text, clean, chunk, and generate embeddings
- 🧠 384-dimensional vector embeddings via `all-MiniLM-L6-v2`
- 📊 Real-time dashboard (documents, pages, words, chunks, embeddings, size)
- 🎨 Cybersecurity-themed dark UI with custom CSS
- 💬 Chat interface (mock responses — LLM integration in next sprint)

---

## Quick Start

### Prerequisites

- Python ≥ 3.10
- pip

### Installation

```bash
# Clone the repo
git clone https://github.com/Roastee/cyber-threat-rag-assistant.git
cd cyber-threat-rag-assistant

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open at **http://localhost:8501**.

---

## Project Structure

```
cyber-threat-rag-assistant/
│
├── app.py                              # Streamlit entry point (thin orchestrator)
├── .streamlit/config.toml              # Streamlit theme configuration
├── .env.example                        # Environment variable template
├── requirements.txt                    # Pinned Python dependencies
├── .gitignore                          # Git ignore rules
├── LICENSE                             # MIT License
├── roadmap.md                          # Sprint development plan
├── tasks.md                            # Task tracker
├── ai_context.md                       # AI assistant context
│
├── src/                                # Source code
│   ├── core/                           # App-wide configuration & state
│   │   ├── config.py                   #   Frozen dataclass config (app, ingestion, embedding, theme)
│   │   └── state.py                    #   Centralized session state manager (typed, no raw st.session_state)
│   │
│   ├── models/                         # Data models (shared across all layers)
│   │   ├── document.py                 #   Document dataclass (extracted PDF content + metadata)
│   │   └── chunk.py                    #   Chunk dataclass (text segment + source metadata, ChromaDB-ready)
│   │
│   ├── ingestion/                      # Document upload & extraction
│   │   ├── pdf_loader.py              #   PyPDF text extraction (per-page, with error handling)
│   │   └── service.py                 #   Ingestion orchestrator: validate → extract → chunk → embed → store
│   │
│   ├── processing/                     # Text cleaning & chunking
│   │   ├── cleaner.py                 #   8-step text normalization (control chars, unicode, PDF line wraps)
│   │   ├── chunker.py                 #   Recursive character splitter (paragraph → line → sentence → word)
│   │   └── pipeline.py               #   Document → Chunks orchestrator with statistics
│   │
│   ├── embeddings/                     # Vector embedding generation
│   │   ├── embedding_service.py       #   sentence-transformers wrapper (provider pattern, lazy loading)
│   │   ├── embedding_pipeline.py      #   Chunks → EmbeddingRecords batch orchestrator
│   │   └── models.py                  #   EmbeddingRecord + EmbeddingStats data models
│   │
│   ├── ui/                             # Streamlit UI components
│   │   ├── styles.py                  #   Custom CSS theme (400+ lines, dark SOC-terminal aesthetic)
│   │   ├── header.py                  #   App header with status indicators
│   │   ├── sidebar.py                #   Navigation + quick settings sidebar
│   │   ├── chat.py                   #   Chat interface with mock responses
│   │   ├── pages.py                  #   Documents / Settings / About page layouts
│   │   └── components.py            #   Reusable widgets (metric cards, badges)
│   │
│   ├── rag/                            # RAG pipeline (not yet implemented)
│   ├── api/                            # FastAPI REST API (not yet implemented)
│   └── utils/                          # Utility functions (not yet implemented)
│
├── tests/                              # Test suite
│   ├── unit/                           #   Unit tests (stubs)
│   └── integration/                    #   Integration tests (stubs)
│
├── data/                               # Data storage
│   ├── raw/feeds/                      #   Threat intelligence feeds
│   ├── raw/reports/                    #   Threat reports (PDFs)
│   └── processed/                      #   Processed chunks
│
├── docs/                               # Documentation
│   ├── architecture.md                #   System architecture
│   ├── changelog.md                   #   Version changelog
│   ├── api/                           #   API reference
│   ├── guides/                        #   User & developer guides
│   └── assets/                        #   Images & diagrams
│
└── scripts/                            # Utility scripts
```

---

## Architecture

```
User uploads PDF
    │
    ▼
┌──────────────────────────────────────────────────┐
│  IngestionService (src/ingestion/service.py)     │
│                                                  │
│  Step 1: Validate (type, size, duplicates)       │
│  Step 2: Extract text (PyPDF, per-page)          │
│  Step 3: Store Document in session state         │
│  Step 4: Clean + Chunk (processing pipeline)     │
│  Step 5: Generate embeddings (sentence-transformers) │
│  Step 6: Store vectors in session state          │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│  [Future] ChromaDB → Vector Search → LLM → RAG  │
└──────────────────────────────────────────────────┘
```

### Layer Separation

| Layer | Package | Responsibility |
|---|---|---|
| **UI** | `src/ui/` | Streamlit components, no business logic |
| **Service** | `src/ingestion/` | Orchestration, validation, business rules |
| **Processing** | `src/processing/` | Text cleaning, chunking (Streamlit-free) |
| **Embeddings** | `src/embeddings/` | Vector generation (provider pattern, model-agnostic) |
| **Models** | `src/models/` | Typed dataclasses shared across all layers |
| **Core** | `src/core/` | Configuration + session state management |

---

## Tech Stack

| Component | Technology | Status |
|---|---|---|
| Language | Python 3.12 | ✅ Active |
| UI Framework | Streamlit 1.45 | ✅ Active |
| PDF Extraction | pypdf 5.6 | ✅ Active |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | ✅ Active |
| State Management | Typed `StateManager` (session_state wrapper) | ✅ Active |
| Vector Store | ChromaDB | ⏳ Next Sprint |
| LLM Provider | OpenAI / Ollama | ⏳ Planned |
| LLM Orchestration | LangChain | ⏳ Planned |
| API Framework | FastAPI | ⏳ Planned |
| Testing | pytest | ⏳ Planned |

---

## Development Progress

| Sprint | Name | Status |
|---|---|---|
| 1 | Project Foundation | ✅ Complete |
| 2 | Streamlit UI | ✅ Complete |
| 3A | PDF Ingestion | ✅ Complete |
| 3B | Text Processing Pipeline | ✅ Complete |
| 4A | Embedding Generation | ✅ Complete |
| 4B | ChromaDB Integration | 🔄 Next |
| 5 | RAG Pipeline + LLM | ⏳ Planned |
| 6 | Intelligence Enhancement | ⏳ Planned |
| 7 | Production Hardening | ⏳ Planned |

---

## Key Design Decisions

- **Clean Architecture** — UI → Service → Processing → Embeddings. Each layer is independently testable.
- **Provider Pattern** — Only `embedding_service.py` imports `sentence_transformers`. Swap to OpenAI/Cohere by changing one file.
- **Typed State** — All state access goes through `StateManager` with typed getters/setters. No raw `st.session_state` in components.
- **ChromaDB-Ready** — `Chunk.metadata` property returns a dict that maps 1:1 to `collection.add(metadatas=[...])`.
- **Lazy Model Loading** — The embedding model (~80MB) loads on first use, not on import. App startup stays instant.

---

## License

MIT — see [LICENSE](LICENSE)

---

> ⚠️ **This project is under active development.** The README will be updated as more features are completed.
