"""
Text chunker — splits cleaned text into retrieval-ready chunks.

Uses a recursive character-splitting strategy that respects document
structure. Splits on increasingly fine-grained separators:

    Priority 1:  \n\n  (paragraph boundary)
    Priority 2:  \n    (line break)
    Priority 3:  .     (sentence boundary — period + space)
    Priority 4:  " "   (word boundary)
    Priority 5:  ""    (character — last resort)

This ensures:
    - Paragraphs stay together when possible
    - Sentences are not broken mid-word
    - Chunks are as close to `chunk_size` as possible without exceeding it

Design Decision — Why character-based, not token-based?
    Token counting requires tiktoken and is model-specific (GPT-4 vs
    Claude vs local models use different tokenizers). Character-based
    chunking is universal. The approximate conversion is:
        1 token ≈ 4 characters (English text)
    So chunk_size=1000 chars ≈ 250 tokens. When the embedding sprint
    arrives, we can adjust chunk_size or add a token-based wrapper
    around this character splitter without changing the interface.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.models.chunk import Chunk

logger = logging.getLogger(__name__)


@dataclass
class ChunkerConfig:
    """Configuration for the text chunker.

    Attributes:
        chunk_size:    Target maximum characters per chunk.
        chunk_overlap: Number of characters to overlap between consecutive chunks.
        separators:    Ordered list of separators to try (most → least preferred).
    """

    chunk_size: int = 1000
    chunk_overlap: int = 200
    separators: tuple[str, ...] = ("\n\n", "\n", ". ", " ", "")

    def __post_init__(self) -> None:
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than "
                f"chunk_size ({self.chunk_size})"
            )
        if self.chunk_size < 50:
            raise ValueError(f"chunk_size ({self.chunk_size}) must be at least 50")


class TextChunker:
    """Splits text into overlapping chunks with metadata.

    Usage:
        chunker = TextChunker(ChunkerConfig(chunk_size=1000, chunk_overlap=200))
        chunks = chunker.chunk(text, doc_id="abc123", filename="report.pdf")
    """

    def __init__(self, config: ChunkerConfig | None = None) -> None:
        self.config = config or ChunkerConfig()

    def chunk(
        self,
        text: str,
        doc_id: str,
        filename: str,
        page_boundaries: list[int] | None = None,
    ) -> list[Chunk]:
        """Split text into chunks with source metadata.

        Args:
            text:             Cleaned text to chunk.
            doc_id:           Parent document ID.
            filename:         Source filename.
            page_boundaries:  Character offsets where each page starts
                              (from cumulative page text lengths). Used to
                              estimate which page a chunk belongs to.

        Returns:
            List of Chunk objects with metadata attached.
        """
        if not text or not text.strip():
            logger.warning("Empty text received for chunking")
            return []

        # Step 1: Split text into raw string segments
        raw_segments = self._recursive_split(text, list(self.config.separators))

        # Step 2: Merge small segments and apply overlap
        merged_texts, offsets = self._merge_with_overlap(raw_segments, text)

        # Step 3: Convert to Chunk objects with metadata
        total_chunks = len(merged_texts)
        chunks: list[Chunk] = []

        for i, (chunk_text, start_offset) in enumerate(zip(merged_texts, offsets)):
            page_num = self._estimate_page(start_offset, page_boundaries)

            chunk = Chunk(
                content=chunk_text,
                doc_id=doc_id,
                filename=filename,
                chunk_index=i,
                total_chunks=total_chunks,
                page_number=page_num,
                start_char=start_offset,
                end_char=start_offset + len(chunk_text),
            )
            chunks.append(chunk)

        logger.info(
            "Chunked '%s': %d chars → %d chunks (size=%d, overlap=%d)",
            filename,
            len(text),
            len(chunks),
            self.config.chunk_size,
            self.config.chunk_overlap,
        )

        return chunks

    # ── Core Algorithm ───────────────────────────────────────

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using the separator hierarchy.

        Tries each separator in order. For each split segment:
        - If the segment fits within chunk_size, keep it.
        - If not, recurse with the next separator.
        """
        if not text:
            return []

        if len(text) <= self.config.chunk_size:
            return [text]

        if not separators:
            # Last resort: hard-cut at chunk_size
            return [
                text[i : i + self.config.chunk_size]
                for i in range(0, len(text), self.config.chunk_size)
            ]

        separator = separators[0]
        remaining_separators = separators[1:]

        if not separator:
            # Empty separator means split by character
            return [
                text[i : i + self.config.chunk_size]
                for i in range(0, len(text), self.config.chunk_size)
            ]

        parts = text.split(separator)
        segments: list[str] = []

        for part in parts:
            part_with_sep = part + separator if part != parts[-1] else part

            if len(part_with_sep) <= self.config.chunk_size:
                segments.append(part_with_sep)
            else:
                # This segment is too large — recurse with finer separator
                sub_segments = self._recursive_split(part_with_sep, remaining_separators)
                segments.extend(sub_segments)

        return [s for s in segments if s.strip()]

    def _merge_with_overlap(
        self,
        segments: list[str],
        original_text: str,
    ) -> tuple[list[str], list[int]]:
        """Merge small segments into chunk_size blocks and add overlap.

        Returns:
            Tuple of (merged_texts, start_offsets).
        """
        if not segments:
            return [], []

        merged: list[str] = []
        offsets: list[int] = []
        current_chunk = ""
        current_offset = 0

        for segment in segments:
            # If adding this segment exceeds chunk_size, finalize current chunk
            if current_chunk and (len(current_chunk) + len(segment)) > self.config.chunk_size:
                merged.append(current_chunk.strip())
                offsets.append(current_offset)

                # Apply overlap: take the last `overlap` chars of current chunk
                overlap_text = current_chunk[-self.config.chunk_overlap :] if self.config.chunk_overlap > 0 else ""
                current_offset = max(0, current_offset + len(current_chunk) - self.config.chunk_overlap)
                current_chunk = overlap_text

            current_chunk += segment

        # Don't forget the last chunk
        if current_chunk.strip():
            merged.append(current_chunk.strip())
            offsets.append(current_offset)

        return merged, offsets

    def _estimate_page(
        self,
        char_offset: int,
        page_boundaries: list[int] | None,
    ) -> int:
        """Estimate which page a character offset belongs to.

        Args:
            char_offset:      Character position in the full cleaned text.
            page_boundaries:  Cumulative character counts per page.
                              e.g., [0, 3200, 6500, 9800] means page 1
                              starts at char 0, page 2 at char 3200, etc.

        Returns:
            1-based page number estimate.
        """
        if not page_boundaries:
            return 0

        for i in range(len(page_boundaries) - 1, -1, -1):
            if char_offset >= page_boundaries[i]:
                return i + 1  # 1-based page number

        return 1


# ── Factory ──────────────────────────────────────────────────

def create_chunker(
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> TextChunker:
    """Create a TextChunker with the given configuration."""
    config = ChunkerConfig(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return TextChunker(config)


# ── Default instance ─────────────────────────────────────────
text_chunker = TextChunker()
