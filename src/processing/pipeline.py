"""
Processing pipeline — orchestrates Document → Cleaner → Chunker → Chunks.

This is the single entry point the UI/service layer calls to process
a Document into retrieval-ready chunks. It:

    1. Extracts full text from the Document
    2. Cleans the text (normalize whitespace, fix line breaks)
    3. Computes page boundary offsets for page estimation
    4. Chunks the cleaned text with overlap
    5. Computes processing statistics
    6. Returns a ProcessingResult with chunks + stats

Design Decision:
    The pipeline is stateless — it takes a Document in and returns
    a ProcessingResult out. It does not touch session state or
    any external storage. The caller (ingestion service or UI)
    decides where to store the results.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.models.document import Document
from src.models.chunk import Chunk
from src.processing.cleaner import TextCleaner, text_cleaner
from src.processing.chunker import TextChunker, ChunkerConfig, create_chunker

logger = logging.getLogger(__name__)


# ── Result Types ─────────────────────────────────────────────


@dataclass
class ProcessingStats:
    """Statistics from a processing run.

    Designed for display in the UI and for logging/debugging.
    """

    original_char_count: int = 0
    cleaned_char_count: int = 0
    reduction_percent: float = 0.0
    total_chunks: int = 0
    avg_chunk_size: float = 0.0
    min_chunk_size: int = 0
    max_chunk_size: int = 0
    total_words: int = 0
    chunk_size_config: int = 0
    chunk_overlap_config: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize for logging / JSON."""
        return {
            "original_chars": self.original_char_count,
            "cleaned_chars": self.cleaned_char_count,
            "reduction_percent": round(self.reduction_percent, 1),
            "total_chunks": self.total_chunks,
            "avg_chunk_size": round(self.avg_chunk_size, 0),
            "min_chunk_size": self.min_chunk_size,
            "max_chunk_size": self.max_chunk_size,
            "total_words": self.total_words,
            "chunk_size_config": self.chunk_size_config,
            "chunk_overlap_config": self.chunk_overlap_config,
        }


@dataclass
class ProcessingResult:
    """Result of processing a Document through the pipeline.

    Attributes:
        success:  Whether processing completed without errors.
        doc_id:   ID of the source document.
        filename: Source filename.
        chunks:   List of Chunk objects produced.
        stats:    Processing statistics.
        error:    Error message if processing failed.
    """

    success: bool
    doc_id: str = ""
    filename: str = ""
    chunks: list[Chunk] = field(default_factory=list)
    stats: ProcessingStats = field(default_factory=ProcessingStats)
    error: str = ""


# ── Pipeline ─────────────────────────────────────────────────


class ProcessingPipeline:
    """Orchestrates the full Document → Chunks processing pipeline.

    Usage:
        pipeline = ProcessingPipeline()
        result = pipeline.process(document)
        if result.success:
            for chunk in result.chunks:
                print(chunk.preview)
    """

    def __init__(
        self,
        cleaner: TextCleaner | None = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        self._cleaner = cleaner or text_cleaner
        self._chunker = create_chunker(chunk_size, chunk_overlap)
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def process(self, document: Document) -> ProcessingResult:
        """Process a Document into retrieval-ready chunks.

        Args:
            document: A Document object from the ingestion layer.

        Returns:
            ProcessingResult with chunks and statistics.
        """
        logger.info("Processing document: %s (ID: %s)", document.filename, document.doc_id)

        try:
            # Step 1: Get raw text
            raw_text = document.content
            if not raw_text or not raw_text.strip():
                logger.warning("Document %s has no text content", document.filename)
                return ProcessingResult(
                    success=False,
                    doc_id=document.doc_id,
                    filename=document.filename,
                    error="Document has no text content to process.",
                )

            original_len = len(raw_text)

            # Step 2: Clean text
            cleaned_text = self._cleaner.clean(raw_text)
            cleaned_len = len(cleaned_text)

            if not cleaned_text.strip():
                return ProcessingResult(
                    success=False,
                    doc_id=document.doc_id,
                    filename=document.filename,
                    error="Text was empty after cleaning.",
                )

            # Step 3: Compute page boundaries for page estimation
            page_boundaries = self._compute_page_boundaries(document.pages)

            # Step 4: Chunk the cleaned text
            chunks = self._chunker.chunk(
                text=cleaned_text,
                doc_id=document.doc_id,
                filename=document.filename,
                page_boundaries=page_boundaries,
            )

            if not chunks:
                return ProcessingResult(
                    success=False,
                    doc_id=document.doc_id,
                    filename=document.filename,
                    error="Chunking produced no chunks.",
                )

            # Step 5: Compute statistics
            stats = self._compute_stats(
                original_len=original_len,
                cleaned_len=cleaned_len,
                chunks=chunks,
            )

            logger.info(
                "Processed %s: %d chars → %d chunks (avg %.0f chars/chunk)",
                document.filename,
                original_len,
                len(chunks),
                stats.avg_chunk_size,
            )

            return ProcessingResult(
                success=True,
                doc_id=document.doc_id,
                filename=document.filename,
                chunks=chunks,
                stats=stats,
            )

        except Exception as e:
            logger.error("Processing failed for %s: %s", document.filename, e)
            return ProcessingResult(
                success=False,
                doc_id=document.doc_id,
                filename=document.filename,
                error=f"Processing failed: {e}",
            )

    def _compute_page_boundaries(self, pages: list[str]) -> list[int]:
        """Compute cumulative character offsets for each page.

        Given pages = ["page1 text", "page2 text"], returns [0, 10]
        meaning page 1 starts at char 0, page 2 starts at char 10.
        """
        if not pages:
            return []

        boundaries: list[int] = [0]
        cumulative = 0
        for page_text in pages[:-1]:
            cumulative += len(page_text) + 2  # +2 for the \n\n between pages
            boundaries.append(cumulative)

        return boundaries

    def _compute_stats(
        self,
        original_len: int,
        cleaned_len: int,
        chunks: list[Chunk],
    ) -> ProcessingStats:
        """Compute processing statistics from the result."""
        chunk_sizes = [c.char_count for c in chunks]
        total_words = sum(c.word_count for c in chunks)

        reduction = ((original_len - cleaned_len) / original_len * 100) if original_len else 0

        return ProcessingStats(
            original_char_count=original_len,
            cleaned_char_count=cleaned_len,
            reduction_percent=reduction,
            total_chunks=len(chunks),
            avg_chunk_size=sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
            min_chunk_size=min(chunk_sizes) if chunk_sizes else 0,
            max_chunk_size=max(chunk_sizes) if chunk_sizes else 0,
            total_words=total_words,
            chunk_size_config=self._chunk_size,
            chunk_overlap_config=self._chunk_overlap,
        )


# ── Factory ──────────────────────────────────────────────────

def create_pipeline(
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> ProcessingPipeline:
    """Create a ProcessingPipeline with the given configuration."""
    return ProcessingPipeline(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


# ── Default instance ─────────────────────────────────────────
processing_pipeline = ProcessingPipeline()
