"""
src.processing — Text cleaning, chunking, and document processing.

Public API:
    - TextCleaner / text_cleaner:     Normalizes raw PDF text.
    - TextChunker / text_chunker:     Splits text into overlapping chunks.
    - ProcessingPipeline:             Full Document → Chunks orchestrator.
    - ProcessingResult:               Result with chunks + statistics.
    - ProcessingStats:                Processing statistics.
    - create_pipeline:                Factory for custom pipeline config.
"""

from src.processing.cleaner import TextCleaner, text_cleaner
from src.processing.chunker import TextChunker, ChunkerConfig, text_chunker, create_chunker
from src.processing.pipeline import (
    ProcessingPipeline,
    ProcessingResult,
    ProcessingStats,
    processing_pipeline,
    create_pipeline,
)

__all__ = [
    "TextCleaner",
    "text_cleaner",
    "TextChunker",
    "ChunkerConfig",
    "text_chunker",
    "create_chunker",
    "ProcessingPipeline",
    "ProcessingResult",
    "ProcessingStats",
    "processing_pipeline",
    "create_pipeline",
]
