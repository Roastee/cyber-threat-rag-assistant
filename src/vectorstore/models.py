"""
Vector store data models.

Defines result types and statistics for ChromaDB operations.
These are Streamlit/ChromaDB-agnostic data containers used
by the collection manager and indexing pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class IndexingResult:
    """Result of indexing chunks into ChromaDB.

    Attributes:
        success:         Whether indexing completed without errors.
        indexed_count:   Number of chunks successfully indexed.
        skipped_count:   Chunks skipped (already in collection).
        failed_count:    Chunks that failed to index.
        doc_id:          Parent document ID.
        collection_name: Target ChromaDB collection name.
        error:           Error message if indexing failed.
        time_secs:       Wall-clock time for the indexing operation.
    """

    success: bool
    indexed_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    doc_id: str = ""
    collection_name: str = ""
    error: str = ""
    time_secs: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "indexed_count": self.indexed_count,
            "skipped_count": self.skipped_count,
            "failed_count": self.failed_count,
            "doc_id": self.doc_id,
            "collection_name": self.collection_name,
            "time_secs": round(self.time_secs, 3),
            "error": self.error,
        }


@dataclass
class CollectionStats:
    """Statistics about a ChromaDB collection.

    Attributes:
        name:           Collection name.
        total_vectors:  Number of vectors stored.
        dimensions:     Embedding dimensionality (0 if empty).
        doc_ids:        Unique document IDs in the collection.
        doc_count:      Number of unique documents.
        metadata_keys:  Available metadata filter fields.
    """

    name: str = ""
    total_vectors: int = 0
    dimensions: int = 0
    doc_ids: list[str] = field(default_factory=list)
    doc_count: int = 0
    metadata_keys: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "total_vectors": self.total_vectors,
            "dimensions": self.dimensions,
            "doc_count": self.doc_count,
            "doc_ids": self.doc_ids,
            "metadata_keys": self.metadata_keys,
        }


@dataclass
class VectorStoreInfo:
    """High-level info about the entire vector store.

    Attributes:
        persist_directory: Path to the ChromaDB storage directory.
        collections:       List of collection names.
        total_vectors:     Total vectors across all collections.
        is_persistent:     Whether data survives restarts.
    """

    persist_directory: str = ""
    collections: list[str] = field(default_factory=list)
    total_vectors: int = 0
    is_persistent: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "persist_directory": self.persist_directory,
            "collections": self.collections,
            "total_vectors": self.total_vectors,
            "is_persistent": self.is_persistent,
        }
