"""
src.embeddings — Vector embedding generation for text chunks.

Public API:
    - EmbeddingService / embedding_service:   Low-level text → vector.
    - EmbeddingPipeline / embedding_pipeline:  Chunks → EmbeddingRecords.
    - EmbeddingRecord:                         Vector + metadata container.
    - EmbeddingStats:                          Run statistics.
    - EmbeddingError:                          Exception type.
"""

from src.embeddings.models import EmbeddingRecord, EmbeddingStats
from src.embeddings.embedding_service import (
    EmbeddingService,
    EmbeddingError,
    embedding_service,
)
from src.embeddings.embedding_pipeline import (
    EmbeddingPipeline,
    EmbeddingPipelineResult,
    embedding_pipeline,
)

__all__ = [
    "EmbeddingService",
    "EmbeddingError",
    "embedding_service",
    "EmbeddingPipeline",
    "EmbeddingPipelineResult",
    "embedding_pipeline",
    "EmbeddingRecord",
    "EmbeddingStats",
]
