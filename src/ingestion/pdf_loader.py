"""
PDF document loader using PyPDF.

Single-responsibility: reads a PDF file buffer and returns a Document.
No Streamlit imports, no state management, no side effects — pure
data transformation. This makes it testable in isolation.

Design Decision:
    We use PyPDF (pypdf) instead of pdfplumber or PyMuPDF because:
    1. Already in requirements.txt (pypdf==5.6.0)
    2. Lightweight — no native dependencies
    3. Good enough for text extraction (no OCR needed at this stage)
    4. Can extract PDF metadata (author, title, creation date)
"""

from __future__ import annotations

import logging
from io import BytesIO
from typing import Any

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from src.models.document import Document

logger = logging.getLogger(__name__)


class PDFLoadError(Exception):
    """Raised when PDF extraction fails."""


class PDFLoader:
    """Extracts text and metadata from PDF files.

    Usage:
        loader = PDFLoader()
        document = loader.load(file_buffer, filename, file_size)
    """

    def load(
        self,
        file_buffer: BytesIO,
        filename: str,
        file_size_bytes: int,
    ) -> Document:
        """Extract text and metadata from a PDF file buffer.

        Args:
            file_buffer:     In-memory file buffer (from st.file_uploader).
            filename:        Original filename.
            file_size_bytes: Size of the file in bytes.

        Returns:
            A Document with extracted content, page texts, and metadata.

        Raises:
            PDFLoadError: If the PDF cannot be read or parsed.
        """
        logger.info("Loading PDF: %s (%.2f KB)", filename, file_size_bytes / 1024)

        try:
            reader = self._create_reader(file_buffer)
            page_count = len(reader.pages)
            logger.info("PDF has %d pages", page_count)

            pages = self._extract_pages(reader, filename)
            content = "\n\n".join(pages)
            metadata = self._extract_metadata(reader)

            status = "success" if content.strip() else "partial"
            error_msg = "" if content.strip() else "No text content extracted (scanned PDF?)"

            if status == "partial":
                logger.warning("No text extracted from %s — may be a scanned PDF", filename)

            document = Document(
                filename=filename,
                content=content,
                page_count=page_count,
                file_size_bytes=file_size_bytes,
                pages=pages,
                metadata=metadata,
                status=status,
                error_message=error_msg,
            )

            logger.info(
                "Successfully loaded %s: %d pages, %d words, %s",
                filename,
                document.page_count,
                document.word_count,
                document.file_size_display,
            )
            return document

        except PdfReadError as e:
            logger.error("Failed to read PDF %s: %s", filename, e)
            raise PDFLoadError(f"Cannot read PDF '{filename}': {e}") from e
        except Exception as e:
            logger.error("Unexpected error loading PDF %s: %s", filename, e)
            raise PDFLoadError(f"Failed to process '{filename}': {e}") from e

    def _create_reader(self, file_buffer: BytesIO) -> PdfReader:
        """Create a PdfReader from a file buffer."""
        file_buffer.seek(0)
        return PdfReader(file_buffer)

    def _extract_pages(self, reader: PdfReader, filename: str) -> list[str]:
        """Extract text from each page, with per-page error handling."""
        pages: list[str] = []

        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
                pages.append(text.strip())
            except Exception as e:
                logger.warning("Error extracting page %d of %s: %s", i + 1, filename, e)
                pages.append("")  # Empty string for failed pages

        return pages

    def _extract_metadata(self, reader: PdfReader) -> dict[str, str]:
        """Extract available PDF metadata fields."""
        metadata: dict[str, str] = {}

        try:
            pdf_meta = reader.metadata
            if pdf_meta is None:
                return metadata

            field_map: dict[str, str] = {
                "/Title": "title",
                "/Author": "author",
                "/Subject": "subject",
                "/Creator": "creator",
                "/Producer": "producer",
            }

            for pdf_key, our_key in field_map.items():
                value = pdf_meta.get(pdf_key)
                if value and str(value).strip():
                    metadata[our_key] = str(value).strip()

        except Exception as e:
            logger.warning("Could not extract PDF metadata: %s", e)

        return metadata


# ── Singleton instance ───────────────────────────────────────
pdf_loader = PDFLoader()
