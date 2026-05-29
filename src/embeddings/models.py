"""
Embedding data models.

Defines the data structures used by the embedding layer:
    - EmbeddingRecord: A single chunk's embedding vector with metadata.
    - EmbeddingStats:  Statistics from an embedding generation run.

Design Decision — Why a separate model, not just list[float]?
    ChromaDB needs (chunk_id, vector) pairs. By wrapping the vector
    in an EmbeddingRecord that also carries the chunk_id, model name,
    and dimensions, we can:
    1. Validate vector dimensions before storing
    2. Track which model generated each embedding
    3. Map directly to ChromaDB's collection.add(embeddings=...) later
    4. Support model migration (re-embed with a different model)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class EmbeddingRecord:
    """A single chunk's embedding vector with tracking metadata.

    Attributes:
        chunk_id:       ID of the chunk this embedding belongs to.
        vector:         The dense embedding vector (list of floats).
        model_name:     Name of the model that generated this embedding.
        dimensions:     Number of dimensions in the vector.
        timestamp:      ISO-8601 timestamp of when the embedding was created.
        doc_id:         Parent document ID (for grouping / filtering).
    """

    chunk_id: str
    vector: list[float]
    model_name: str
    dimensions: int
    doc_id: str = ""

    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        """Validate that dimensions match vector length."""
        if self.dimensions == 0 and self.vector:
            self.dimensions = len(self.vector)
        if self.vector and len(self.vector) != self.dimensions:
            raise ValueError(
                f"Vector length ({len(self.vector)}) does not match "
                f"declared dimensions ({self.dimensions})"
            )

    @property
    def vector_preview(self) -> str:
        """First 5 values of the vector for display."""
        if not self.vector:
            return "[]"
        preview = ", ".join(f"{v:.6f}" for v in self.vector[:5])
        return f"[{preview}, ...] ({self.dimensions}d)"

    def to_dict(self) -> dict[str, Any]:
        """Serialize for logging (excludes the full vector for brevity)."""
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "model_name": self.model_name,
            "dimensions": self.dimensions,
            "timestamp": self.timestamp,
            "vector_preview": self.vector_preview,
        }


@dataclass
class EmbeddingStats:
    """Statistics from an embedding generation run.

    Attributes:
        total_chunks:     Number of chunks that were embedded.
        model_name:       Embedding model used.
        dimensions:       Vector dimensionality.
        total_time_secs:  Total wall-clock time for the run.
        chunks_per_sec:   Throughput in chunks per second.
        batch_size:       Batch size used during encoding.
        doc_id:           Document ID (if processing a single document).
    """

    total_chunks: int = 0
    model_name: str = ""
    dimensions: int = 0
    total_time_secs: float = 0.0
    chunks_per_sec: float = 0.0
    batch_size: int = 0
    doc_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize for display / logging."""
        return {
            "total_chunks": self.total_chunks,
            "model_name": self.model_name,
            "dimensions": self.dimensions,
            "total_time_secs": round(self.total_time_secs, 2),
            "chunks_per_sec": round(self.chunks_per_sec, 1),
            "batch_size": self.batch_size,
            "doc_id": self.doc_id,
        }
