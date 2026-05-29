"""
Session state management module.

Provides a clean abstraction over Streamlit's st.session_state.
All state initialization, access, and mutation goes through this module
to keep components stateless and testable.

Design Decision:
    Instead of scattering st.session_state["key"] across components,
    we define a typed StateManager that initializes defaults and exposes
    getter/setter methods. This makes state dependencies explicit and
    makes future migration to a backend-backed state trivial.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import streamlit as st

from src.core.config import app_config
from src.models.document import Document
from src.models.chunk import Chunk
from src.embeddings.models import EmbeddingRecord, EmbeddingStats


# ── Data Models ──────────────────────────────────────────────


@dataclass
class ChatMessage:
    """A single chat message with metadata."""

    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    message_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    sources: list[str] = field(default_factory=list)  # For future RAG citations
    confidence: float | None = None  # For future confidence scoring


@dataclass
class SessionConfig:
    """User-adjustable session settings."""

    model: str = "gpt-4"
    temperature: float = 0.1
    top_k: int = 5
    system_prompt: str = ""

    def __post_init__(self) -> None:
        if not self.system_prompt:
            self.system_prompt = app_config.SYSTEM_PROMPT


# ── State Keys ───────────────────────────────────────────────
# Central registry of all session state keys to prevent typos
# and make dependencies explicit.

class StateKeys:
    """Registry of all session state key names."""

    CHAT_HISTORY = "chat_history"
    SESSION_CONFIG = "session_config"
    CURRENT_PAGE = "current_page"
    SESSION_ID = "session_id"
    INGESTED_DOCS = "ingested_docs"
    INGESTED_DOCS_CONTENT = "ingested_docs_content"
    PROCESSED_CHUNKS = "processed_chunks"
    EMBEDDING_RECORDS = "embedding_records"
    EMBEDDING_STATS = "embedding_stats"
    IS_PROCESSING = "is_processing"
    THEME_MODE = "theme_mode"
    CONVERSATION_COUNT = "conversation_count"


# ── State Manager ────────────────────────────────────────────


class StateManager:
    """
    Manages all Streamlit session state operations.

    Provides typed access to session state with automatic
    initialization of defaults on first run.

    Usage:
        state = StateManager()
        state.initialize()  # Call once at app start
        history = state.get_chat_history()
        state.add_message(ChatMessage(role="user", content="Hello"))
    """

    def initialize(self) -> None:
        """Initialize all session state keys with defaults.

        Safe to call multiple times — only sets values that
        don't already exist (idempotent).
        """
        defaults: dict[str, Any] = {
            StateKeys.CHAT_HISTORY: [],
            StateKeys.SESSION_CONFIG: SessionConfig(),
            StateKeys.CURRENT_PAGE: "chat",
            StateKeys.SESSION_ID: uuid.uuid4().hex[:16],
            StateKeys.INGESTED_DOCS: [],
            StateKeys.INGESTED_DOCS_CONTENT: {},
            StateKeys.PROCESSED_CHUNKS: {},
            StateKeys.EMBEDDING_RECORDS: {},
            StateKeys.EMBEDDING_STATS: {},
            StateKeys.IS_PROCESSING: False,
            StateKeys.THEME_MODE: "dark",
            StateKeys.CONVERSATION_COUNT: 0,
        }
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    # ── Chat History ─────────────────────────────────────────

    def get_chat_history(self) -> list[ChatMessage]:
        """Return the current chat history."""
        return st.session_state.get(StateKeys.CHAT_HISTORY, [])

    def add_message(self, message: ChatMessage) -> None:
        """Append a message to chat history."""
        history: list[ChatMessage] = st.session_state[StateKeys.CHAT_HISTORY]
        history.append(message)

        # Enforce max history limit
        if len(history) > app_config.MAX_CHAT_HISTORY:
            st.session_state[StateKeys.CHAT_HISTORY] = history[
                -app_config.MAX_CHAT_HISTORY :
            ]

    def clear_chat_history(self) -> None:
        """Clear all chat messages and reset conversation count."""
        st.session_state[StateKeys.CHAT_HISTORY] = []
        st.session_state[StateKeys.CONVERSATION_COUNT] = 0

    # ── Session Config ───────────────────────────────────────

    def get_session_config(self) -> SessionConfig:
        """Return the current session configuration."""
        return st.session_state.get(StateKeys.SESSION_CONFIG, SessionConfig())

    def update_session_config(self, **kwargs: Any) -> None:
        """Update session config fields."""
        config: SessionConfig = st.session_state[StateKeys.SESSION_CONFIG]
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

    # ── Navigation ───────────────────────────────────────────

    def get_current_page(self) -> str:
        """Return the current page identifier."""
        return st.session_state.get(StateKeys.CURRENT_PAGE, "chat")

    def set_current_page(self, page: str) -> None:
        """Set the current page."""
        st.session_state[StateKeys.CURRENT_PAGE] = page

    # ── Processing State ─────────────────────────────────────

    def is_processing(self) -> bool:
        """Check if the app is currently processing a query."""
        return st.session_state.get(StateKeys.IS_PROCESSING, False)

    def set_processing(self, value: bool) -> None:
        """Set the processing state."""
        st.session_state[StateKeys.IS_PROCESSING] = value

    # ── Document Tracking ─────────────────────────────────────

    def get_ingested_docs(self) -> list[Document]:
        """Return list of ingested Documents."""
        return st.session_state.get(StateKeys.INGESTED_DOCS, [])

    def add_ingested_doc(self, document: Document) -> None:
        """Store an ingested Document in session state."""
        st.session_state[StateKeys.INGESTED_DOCS].append(document)
        # Also store content keyed by doc_id for fast lookup
        st.session_state[StateKeys.INGESTED_DOCS_CONTENT][document.doc_id] = {
            "content": document.content,
            "pages": document.pages,
        }

    def remove_ingested_doc(self, doc_id: str) -> bool:
        """Remove a document by its ID. Returns True if found and removed."""
        docs: list[Document] = st.session_state[StateKeys.INGESTED_DOCS]
        original_len = len(docs)
        st.session_state[StateKeys.INGESTED_DOCS] = [
            d for d in docs if d.doc_id != doc_id
        ]
        # Remove content too
        st.session_state[StateKeys.INGESTED_DOCS_CONTENT].pop(doc_id, None)
        return len(st.session_state[StateKeys.INGESTED_DOCS]) < original_len

    def clear_ingested_docs(self) -> None:
        """Remove all ingested documents."""
        st.session_state[StateKeys.INGESTED_DOCS] = []
        st.session_state[StateKeys.INGESTED_DOCS_CONTENT] = {}

    def get_total_ingested_words(self) -> int:
        """Return total word count across all ingested documents."""
        return sum(doc.word_count for doc in self.get_ingested_docs())

    def get_document_content(self, doc_id: str) -> str | None:
        """Retrieve the full text content for a document by ID."""
        data = st.session_state.get(StateKeys.INGESTED_DOCS_CONTENT, {}).get(doc_id)
        return data["content"] if data else None

    # ── Chunk Storage ────────────────────────────────────────

    def store_chunks(self, doc_id: str, chunks: list[Chunk]) -> None:
        """Store processed chunks for a document."""
        st.session_state[StateKeys.PROCESSED_CHUNKS][doc_id] = chunks

    def get_chunks(self, doc_id: str) -> list[Chunk]:
        """Retrieve chunks for a specific document."""
        return st.session_state.get(StateKeys.PROCESSED_CHUNKS, {}).get(doc_id, [])

    def get_all_chunks(self) -> list[Chunk]:
        """Retrieve all chunks across all documents."""
        all_chunks: list[Chunk] = []
        for chunks in st.session_state.get(StateKeys.PROCESSED_CHUNKS, {}).values():
            all_chunks.extend(chunks)
        return all_chunks

    def get_total_chunk_count(self) -> int:
        """Return total number of chunks across all documents."""
        return sum(
            len(chunks)
            for chunks in st.session_state.get(StateKeys.PROCESSED_CHUNKS, {}).values()
        )

    def clear_chunks(self, doc_id: str | None = None) -> None:
        """Clear chunks for a specific document, or all chunks if doc_id is None."""
        if doc_id:
            st.session_state.get(StateKeys.PROCESSED_CHUNKS, {}).pop(doc_id, None)
        else:
            st.session_state[StateKeys.PROCESSED_CHUNKS] = {}

    # ── Embedding Storage ─────────────────────────────────────

    def store_embeddings(
        self,
        doc_id: str,
        records: list[EmbeddingRecord],
        stats: EmbeddingStats,
    ) -> None:
        """Store embedding records and stats for a document."""
        st.session_state[StateKeys.EMBEDDING_RECORDS][doc_id] = records
        st.session_state[StateKeys.EMBEDDING_STATS][doc_id] = stats

    def get_embeddings(self, doc_id: str) -> list[EmbeddingRecord]:
        """Retrieve embedding records for a specific document."""
        return st.session_state.get(StateKeys.EMBEDDING_RECORDS, {}).get(doc_id, [])

    def get_embedding_stats(self, doc_id: str) -> EmbeddingStats | None:
        """Retrieve embedding stats for a specific document."""
        return st.session_state.get(StateKeys.EMBEDDING_STATS, {}).get(doc_id)

    def get_total_embedding_count(self) -> int:
        """Return total number of embeddings across all documents."""
        return sum(
            len(records)
            for records in st.session_state.get(StateKeys.EMBEDDING_RECORDS, {}).values()
        )

    def has_embeddings(self, doc_id: str) -> bool:
        """Check if a document has embeddings generated."""
        return bool(st.session_state.get(StateKeys.EMBEDDING_RECORDS, {}).get(doc_id))

    def clear_embeddings(self, doc_id: str | None = None) -> None:
        """Clear embeddings for a specific document, or all if doc_id is None."""
        if doc_id:
            st.session_state.get(StateKeys.EMBEDDING_RECORDS, {}).pop(doc_id, None)
            st.session_state.get(StateKeys.EMBEDDING_STATS, {}).pop(doc_id, None)
        else:
            st.session_state[StateKeys.EMBEDDING_RECORDS] = {}
            st.session_state[StateKeys.EMBEDDING_STATS] = {}

    # ── Session Metadata ─────────────────────────────────────

    def get_session_id(self) -> str:
        """Return the current session ID."""
        return st.session_state.get(StateKeys.SESSION_ID, "unknown")

    def increment_conversation_count(self) -> int:
        """Increment and return the conversation turn count."""
        st.session_state[StateKeys.CONVERSATION_COUNT] += 1
        return st.session_state[StateKeys.CONVERSATION_COUNT]


# ── Singleton instance ───────────────────────────────────────
state_manager = StateManager()
