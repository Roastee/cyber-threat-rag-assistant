"""
Embedding pipeline — orchestrates Chunks → EmbeddingRecords.

Takes a list of Chunk objects (from the processing pipeline),
extracts their text content, sends them through the EmbeddingService
in optimized batches, and returns EmbeddingRecord objects with
full metadata attached.

Architecture:
    Chunks ──→ EmbeddingPipeline.embed_chunks()
                    │
                    ├─ Extract texts from chunks
                    ├─ Batch embed via EmbeddingService
                    ├─ Wrap in EmbeddingRecord (chunk_id + vector + metadata)
                    ├─ Compute EmbeddingStats
                    │
                    └─→ EmbeddingPipelineResult (records + stats)

Design Decision — Why a pipeline on top of the service?
    The EmbeddingService is model-focused (text → vector).
    The pipeline is application-focused (chunks → records with metadata).
    This separation means:
    - The service can be reused for query embedding (single text)
    - The pipeline handles batch orchestration and metadata attachment
    - The pipeline computes throughput stats for the UI
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from src.models.chunk import Chunk
from src.embeddings.models import EmbeddingRecord, EmbeddingStats
from src.embeddings.embedding_service import (
    EmbeddingService,
    EmbeddingError,
    embedding_service,
)

logger = logging.getLogger(__name__)


# ── Result Type ──────────────────────────────────────────────


@dataclass
class EmbeddingPipelineResult:
    """Result of embedding a set of chunks.

    Attributes:
        success:  Whether embedding completed without errors.
        records:  List of EmbeddingRecord objects produced.
        stats:    Performance and configuration statistics.
        error:    Error message if embedding failed.
    """

    success: bool
    records: list[EmbeddingRecord] = field(default_factory=list)
    stats: EmbeddingStats = field(default_factory=EmbeddingStats)
    error: str = ""


# ── Pipeline ─────────────────────────────────────────────────


class EmbeddingPipeline:
    """Orchestrates chunk embedding with metadata and statistics.

    Usage:
        pipeline = EmbeddingPipeline()
        result = pipeline.embed_chunks(chunks, doc_id="abc123")
        if result.success:
            for record in result.records:
                print(record.chunk_id, record.vector_preview)
    """

    def __init__(self, service: EmbeddingService | None = None) -> None:
        self._service = service or embedding_service

    def embed_chunks(
        self,
        chunks: list[Chunk],
        doc_id: str = "",
    ) -> EmbeddingPipelineResult:
        """Embed a list of chunks and return records with metadata.

        Args:
            chunks: List of Chunk objects to embed.
            doc_id: Parent document ID for grouping.

        Returns:
            EmbeddingPipelineResult with records and statistics.
        """
        if not chunks:
            return EmbeddingPipelineResult(
                success=False,
                error="No chunks provided for embedding.",
            )

        logger.info(
            "Starting embedding for %d chunks (doc_id=%s, model=%s)",
            len(chunks),
            doc_id or "all",
            self._service.model_name,
        )

        start_time = time.perf_counter()

        try:
            # Step 1: Extract text content from chunks
            texts = [chunk.content for chunk in chunks]

            # Step 2: Batch embed all texts
            vectors = self._service.embed_batch(texts)

            # Step 3: Wrap in EmbeddingRecord objects
            records: list[EmbeddingRecord] = []
            for chunk, vector in zip(chunks, vectors):
                record = EmbeddingRecord(
                    chunk_id=chunk.chunk_id,
                    vector=vector,
                    model_name=self._service.model_name,
                    dimensions=len(vector),
                    doc_id=chunk.doc_id,
                )
                records.append(record)

            # Step 4: Compute statistics
            elapsed = time.perf_counter() - start_time
            stats = EmbeddingStats(
                total_chunks=len(records),
                model_name=self._service.model_name,
                dimensions=self._service.dimensions,
                total_time_secs=elapsed,
                chunks_per_sec=len(records) / elapsed if elapsed > 0 else 0,
                batch_size=self._service.batch_size,
                doc_id=doc_id,
            )

            logger.info(
                "Embedded %d chunks in %.2fs (%.1f chunks/sec, %dd vectors)",
                stats.total_chunks,
                stats.total_time_secs,
                stats.chunks_per_sec,
                stats.dimensions,
            )

            return EmbeddingPipelineResult(
                success=True,
                records=records,
                stats=stats,
            )

        except EmbeddingError as e:
            logger.error("Embedding failed: %s", e)
            return EmbeddingPipelineResult(success=False, error=str(e))
        except Exception as e:
            logger.error("Unexpected embedding error: %s", e)
            return EmbeddingPipelineResult(
                success=False,
                error=f"Embedding failed: {e}",
            )


# ── Singleton ────────────────────────────────────────────────

embedding_pipeline = EmbeddingPipeline()
