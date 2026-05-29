"""
Document ingestion service — orchestrates the upload pipeline.

This is the single entry point that the UI layer calls. It:
    1. Validates the uploaded file (type, size)
    2. Delegates extraction to the appropriate loader (PDFLoader)
    3. Stores the resulting Document in session state
    4. Returns the Document to the caller for immediate display

Design Decision:
    The service is Streamlit-agnostic in its logic but does call
    StateManager for persistence. This keeps the UI layer thin
    (just file_uploader + display) while the service owns all
    business rules (validation, size limits, allowed types).

    In a future sprint, this service will also:
    - Store vectors in ChromaDB
    But NOT today — we extract, chunk, embed, and store in session state.
"""

from __future__ import annotations

import logging
from io import BytesIO
from dataclasses import dataclass

from src.core.config import app_config
from src.core.state import state_manager
from src.ingestion.pdf_loader import PDFLoader, PDFLoadError
from src.models.document import Document
from src.processing.pipeline import processing_pipeline, ProcessingStats
from src.embeddings.embedding_pipeline import embedding_pipeline

logger = logging.getLogger(__name__)


# ── Result Types ─────────────────────────────────────────────


@dataclass
class IngestionResult:
    """Result of a document ingestion attempt.

    Attributes:
        success:  Whether the ingestion completed without errors.
        document: The extracted Document (None if failed).
        error:    Human-readable error message (empty if success).
    """

    success: bool
    document: Document | None = None
    error: str = ""
    chunk_count: int = 0
    embedding_count: int = 0
    processing_stats: ProcessingStats | None = None


# ── Validation Errors ────────────────────────────────────────


class ValidationError(Exception):
    """Raised when file validation fails before extraction."""


# ── Service ──────────────────────────────────────────────────


class IngestionService:
    """Orchestrates the document ingestion pipeline.

    Usage:
        service = IngestionService()
        result = service.ingest_pdf(file_buffer, filename, file_size)
        if result.success:
            print(result.document.word_count)
    """

    ALLOWED_EXTENSIONS: set[str] = {".pdf"}
    MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB

    def __init__(self) -> None:
        self._pdf_loader = PDFLoader()

    def ingest_pdf(
        self,
        file_buffer: BytesIO,
        filename: str,
        file_size_bytes: int,
    ) -> IngestionResult:
        """Validate, extract, and store a PDF document.

        Args:
            file_buffer:     In-memory file content.
            filename:        Original filename.
            file_size_bytes: File size in bytes.

        Returns:
            IngestionResult with success/failure status and the Document.
        """
        logger.info("Starting ingestion for: %s", filename)

        # Step 1: Validate
        try:
            self._validate_file(filename, file_size_bytes)
        except ValidationError as e:
            logger.warning("Validation failed for %s: %s", filename, e)
            return IngestionResult(success=False, error=str(e))

        # Step 2: Check for duplicates
        if self._is_duplicate(filename):
            msg = f"Document '{filename}' is already ingested."
            logger.info(msg)
            return IngestionResult(success=False, error=msg)

        # Step 3: Extract
        try:
            document = self._pdf_loader.load(file_buffer, filename, file_size_bytes)
        except PDFLoadError as e:
            logger.error("Extraction failed for %s: %s", filename, e)
            return IngestionResult(success=False, error=str(e))

        # Step 4: Store in session state
        state_manager.add_ingested_doc(document)

        # Step 5: Process (clean + chunk)
        chunk_count = 0
        proc_stats = None
        try:
            proc_result = processing_pipeline.process(document)
            if proc_result.success:
                state_manager.store_chunks(document.doc_id, proc_result.chunks)
                chunk_count = len(proc_result.chunks)
                proc_stats = proc_result.stats
                logger.info(
                    "Processed %s: %d chunks (avg %.0f chars)",
                    filename,
                    chunk_count,
                    proc_result.stats.avg_chunk_size,
                )
            else:
                logger.warning("Processing failed for %s: %s", filename, proc_result.error)
        except Exception as e:
            logger.warning("Processing error for %s (document still stored): %s", filename, e)

        # Step 6: Generate embeddings
        embedding_count = 0
        if proc_result and proc_result.success and proc_result.chunks:
            try:
                emb_result = embedding_pipeline.embed_chunks(
                    proc_result.chunks, doc_id=document.doc_id
                )
                if emb_result.success:
                    state_manager.store_embeddings(
                        document.doc_id, emb_result.records, emb_result.stats
                    )
                    embedding_count = len(emb_result.records)
                    logger.info(
                        "Embedded %s: %d vectors (%dd, %.1f chunks/sec)",
                        filename,
                        embedding_count,
                        emb_result.stats.dimensions,
                        emb_result.stats.chunks_per_sec,
                    )
                else:
                    logger.warning("Embedding failed for %s: %s", filename, emb_result.error)
            except Exception as e:
                logger.warning("Embedding error for %s (chunks still stored): %s", filename, e)

        logger.info(
            "Ingestion complete for %s — %d pages, %d words, %d chunks, %d embeddings",
            filename,
            document.page_count,
            document.word_count,
            chunk_count,
            embedding_count,
        )

        return IngestionResult(
            success=True,
            document=document,
            chunk_count=chunk_count,
            embedding_count=embedding_count,
            processing_stats=proc_stats,
        )

    def _validate_file(self, filename: str, file_size_bytes: int) -> None:
        """Validate file type and size.

        Raises:
            ValidationError: If the file doesn't meet requirements.
        """
        # Check extension
        ext = self._get_extension(filename)
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"Unsupported file type: '{ext}'. Only PDF files are accepted."
            )

        # Check size
        if file_size_bytes > self.MAX_FILE_SIZE_BYTES:
            max_mb = self.MAX_FILE_SIZE_BYTES / (1024 * 1024)
            actual_mb = file_size_bytes / (1024 * 1024)
            raise ValidationError(
                f"File too large: {actual_mb:.1f} MB (maximum: {max_mb:.0f} MB)."
            )

        # Check not empty
        if file_size_bytes == 0:
            raise ValidationError("File is empty (0 bytes).")

    def _is_duplicate(self, filename: str) -> bool:
        """Check if a document with the same filename is already ingested."""
        existing_docs = state_manager.get_ingested_docs()
        return any(doc.filename == filename for doc in existing_docs)

    @staticmethod
    def _get_extension(filename: str) -> str:
        """Extract lowercase file extension including the dot."""
        dot_index = filename.rfind(".")
        if dot_index == -1:
            return ""
        return filename[dot_index:].lower()


# ── Singleton instance ───────────────────────────────────────
ingestion_service = IngestionService()
