"""
ChromaDB service — low-level ChromaDB client wrapper.

This is the ONLY module that imports chromadb. All other code
interacts with the vector store through CollectionManager (which
uses this service internally).

Responsibilities:
    - Initialize the persistent ChromaDB client
    - Manage the persist directory
    - Provide the raw client for CollectionManager

Design Decision — Why a separate service?
    Same reasoning as EmbeddingService: if we ever migrate from
    ChromaDB to Pinecone, Weaviate, or Qdrant, we change this
    file and CollectionManager. No other file changes.

Persistence:
    ChromaDB stores data in a local directory (SQLite + Parquet).
    By default we use `./chroma_db/` relative to the project root.
    Data survives app restarts — no re-embedding needed.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────

DEFAULT_PERSIST_DIR: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "chroma_db",
)
DEFAULT_COLLECTION_NAME: str = "threat_intel_docs"


class ChromaService:
    """Low-level ChromaDB client wrapper with persistent storage.

    Usage:
        service = ChromaService()
        client = service.client  # Lazy-loaded persistent client
    """

    def __init__(self, persist_directory: str = DEFAULT_PERSIST_DIR) -> None:
        self._persist_directory = persist_directory
        self._client: Any = None

    @property
    def persist_directory(self) -> str:
        """Path where ChromaDB stores data on disk."""
        return self._persist_directory

    @property
    def client(self) -> Any:
        """Lazy-loaded persistent ChromaDB client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    @property
    def is_initialized(self) -> bool:
        """Whether the client has been created."""
        return self._client is not None

    def _create_client(self) -> Any:
        """Create a persistent ChromaDB client.

        Creates the persist directory if it doesn't exist.
        """
        logger.info("Initializing ChromaDB (persist_dir=%s)", self._persist_directory)

        # Ensure directory exists
        Path(self._persist_directory).mkdir(parents=True, exist_ok=True)

        try:
            import chromadb
            from chromadb.config import Settings

            client = chromadb.PersistentClient(
                path=self._persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )

            logger.info("ChromaDB client ready (persistent mode)")
            return client

        except ImportError as e:
            raise ChromaDBError(
                "chromadb is not installed. Run: pip install chromadb"
            ) from e
        except Exception as e:
            raise ChromaDBError(f"Failed to initialize ChromaDB: {e}") from e

    def list_collections(self) -> list[str]:
        """Return names of all collections."""
        try:
            collections = self.client.list_collections()
            return [c.name for c in collections]
        except Exception as e:
            logger.error("Failed to list collections: %s", e)
            return []

    def reset(self) -> None:
        """Reset the entire database (delete all collections and data).

        WARNING: This is destructive and irreversible.
        """
        logger.warning("Resetting entire ChromaDB database!")
        self.client.reset()

    def heartbeat(self) -> int:
        """Check if ChromaDB is responsive. Returns nanosecond timestamp."""
        return self.client.heartbeat()


# ── Exceptions ───────────────────────────────────────────────


class ChromaDBError(Exception):
    """Raised when a ChromaDB operation fails."""


# ── Singleton ────────────────────────────────────────────────

chroma_service = ChromaService()
