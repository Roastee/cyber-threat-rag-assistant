# 🏗️ Architecture — Threat Intelligence RAG Chatbot

> **Status:** Draft — Sprint 1 scaffold
> **Last Updated:** 2026-05-29

---

## 1. System Overview

The Threat Intelligence RAG Chatbot follows a **Retrieval-Augmented Generation (RAG)** architecture pattern. Instead of relying solely on an LLM's training data, the system retrieves relevant context from a curated vector store of threat intelligence documents before generating responses.

```
User Query
    │
    ▼
┌──────────┐     ┌──────────────┐     ┌──────────┐
│  FastAPI  │────▶│  RAG Chain   │────▶│  LLM     │
│  API      │     │  (LangChain) │     │  (GPT-4) │
└──────────┘     └──────┬───────┘     └──────────┘
                        │                    ▲
                        ▼                    │
                 ┌──────────────┐     ┌──────┴───────┐
                 │  Retriever   │────▶│  Prompt +    │
                 │  (ChromaDB)  │     │  Context     │
                 └──────────────┘     └──────────────┘
                        ▲
                        │
                 ┌──────────────┐
                 │  Ingestion   │
                 │  Pipeline    │
                 └──────┬───────┘
                        │
                 ┌──────────────┐
                 │  Raw Docs    │
                 │  (PDF/DOCX)  │
                 └──────────────┘
```

---

## 2. Component Breakdown

### 2.1 Ingestion Pipeline (`src/ingestion/`)

_To be implemented in Sprint 2._

- Document loading (PDF, DOCX, TXT, HTML)
- Text cleaning & preprocessing
- Chunking with configurable size and overlap
- Metadata extraction (source, date, type)

### 2.2 Vector Store (`ChromaDB`)

_To be implemented in Sprint 2._

- Persistent local storage
- Embedding via OpenAI `text-embedding-3-small`
- Collection management (add, query, delete)

### 2.3 RAG Pipeline (`src/rag/`)

_To be implemented in Sprint 2–3._

- Query embedding
- Similarity search with top-k retrieval
- Prompt template with retrieved context
- LLM generation with source citations

### 2.4 API Layer (`src/api/`)

_To be implemented in Sprint 3._

- FastAPI application
- `/chat` — conversational query endpoint
- `/ingest` — document upload endpoint
- `/health` — health check endpoint
- OpenAPI auto-documentation

### 2.5 Configuration (`src/core/`)

_To be implemented in Sprint 2._

- Environment-based settings via `pydantic-settings`
- Custom exception hierarchy
- Application constants

---

## 3. Data Flow

```
1. INGEST:  Document → Loader → Chunker → Embedder → ChromaDB
2. QUERY:   User Query → Embedder → ChromaDB Search → Top-K Chunks
3. GENERATE: Chunks + Query → Prompt Template → LLM → Cited Response
```

---

## 4. Technology Decisions

| Decision | Choice | Rationale |
|---|---|---|
| LLM Orchestration | LangChain | Mature ecosystem, chain abstractions, easy provider swapping |
| Vector Store | ChromaDB | Zero-config local dev, persistent storage, good Python API |
| API Framework | FastAPI | Async-native, Pydantic integration, auto-docs |
| Embeddings | OpenAI | High quality, easy API, can swap to local models later |
| Config | pydantic-settings | Type-safe, validation, `.env` support |

---

> _This document will be expanded as implementation progresses._
