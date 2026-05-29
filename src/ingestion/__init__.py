"""
src.ingestion — Document loading and preprocessing.

Public API:
    - IngestionService:  Orchestrates file validation → extraction → storage.
    - ingestion_service: Singleton instance ready to use.
    - PDFLoader:         Low-level PDF text extraction.
    - PDFLoadError:      Exception for PDF loading failures.
"""

from src.ingestion.pdf_loader import PDFLoader, PDFLoadError, pdf_loader
from src.ingestion.service import IngestionService, IngestionResult, ingestion_service

__all__ = [
    "IngestionService",
    "IngestionResult",
    "ingestion_service",
    "PDFLoader",
    "PDFLoadError",
    "pdf_loader",
]
