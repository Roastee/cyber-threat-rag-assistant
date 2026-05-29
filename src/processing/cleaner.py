"""
Text cleaner — normalizes extracted PDF text for chunking.

PDFs produce messy text: excessive whitespace, broken line breaks,
inconsistent spacing, header/footer artifacts. This module normalizes
the text while preserving the document's logical structure (paragraphs,
section headers, lists).

Design Decision — Why clean BEFORE chunking?
    If we chunk raw PDF text, chunks will contain garbage whitespace
    that wastes token budget and reduces retrieval quality. Cleaning
    first ensures every chunk is dense with real content.

    We intentionally preserve double-newlines (\n\n) because they
    mark paragraph boundaries — the chunker uses these as the
    primary split point to keep paragraphs together.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


class TextCleaner:
    """Normalizes raw extracted text for downstream processing.

    Usage:
        cleaner = TextCleaner()
        clean_text = cleaner.clean(raw_text)
    """

    def clean(self, text: str) -> str:
        """Run the full cleaning pipeline on raw text.

        Pipeline steps (in order):
            1. Replace null bytes and control characters
            2. Normalize unicode whitespace to ASCII
            3. Fix broken line breaks (PDF mid-word wrapping)
            4. Normalize line endings to \n
            5. Collapse excessive blank lines to max 2 newlines
            6. Normalize horizontal whitespace (tabs, multi-space)
            7. Strip leading/trailing whitespace per line
            8. Strip leading/trailing whitespace on full text

        Args:
            text: Raw extracted text from PDFLoader.

        Returns:
            Cleaned text with preserved paragraph structure.
        """
        if not text or not text.strip():
            logger.warning("Received empty text for cleaning")
            return ""

        original_len = len(text)

        text = self._remove_control_chars(text)
        text = self._normalize_unicode_whitespace(text)
        text = self._fix_broken_line_breaks(text)
        text = self._normalize_line_endings(text)
        text = self._collapse_blank_lines(text)
        text = self._normalize_horizontal_whitespace(text)
        text = self._strip_lines(text)
        text = text.strip()

        cleaned_len = len(text)
        reduction = ((original_len - cleaned_len) / original_len * 100) if original_len else 0

        logger.info(
            "Text cleaned: %d → %d chars (%.1f%% reduction)",
            original_len,
            cleaned_len,
            reduction,
        )

        return text

    # ── Pipeline Steps ───────────────────────────────────────

    def _remove_control_chars(self, text: str) -> str:
        """Remove null bytes and non-printable control characters.

        Preserves: \n (newline), \r (carriage return), \t (tab).
        """
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    def _normalize_unicode_whitespace(self, text: str) -> str:
        """Replace unicode whitespace variants with ASCII equivalents.

        PDFs often contain \xa0 (non-breaking space), \u2003 (em space),
        \u2002 (en space), etc.
        """
        # Non-breaking and special spaces → regular space
        text = re.sub(r"[\xa0\u2000-\u200b\u2028\u2029\u202f\u205f\u3000]", " ", text)
        return text

    def _fix_broken_line_breaks(self, text: str) -> str:
        """Rejoin lines that were broken mid-sentence by PDF extraction.

        Pattern: a lowercase letter or comma at end of line, followed
        by a lowercase letter at the start of the next line. This is
        a soft line break inserted by the PDF renderer, not a real
        paragraph break.

        Example:
            "The malware was distribu-\nted via email" → "The malware was distributed via email"
            "connection to the C2\nserver was established" → "connection to the C2 server was established"
        """
        # Fix hyphenated line breaks: "distribu-\nted" → "distributed"
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

        # Rejoin soft-wrapped lines (lowercase/comma → lowercase)
        text = re.sub(r"([a-z,])\n([a-z])", r"\1 \2", text)

        return text

    def _normalize_line_endings(self, text: str) -> str:
        """Convert all line ending styles to Unix \n."""
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")
        return text

    def _collapse_blank_lines(self, text: str) -> str:
        """Collapse 3+ consecutive newlines to exactly 2 (paragraph break).

        Preserves single \n (line break within a paragraph) and
        double \n\n (paragraph separator).
        """
        return re.sub(r"\n{3,}", "\n\n", text)

    def _normalize_horizontal_whitespace(self, text: str) -> str:
        """Collapse multiple spaces/tabs to a single space."""
        # Tabs to spaces
        text = text.replace("\t", " ")
        # Multiple spaces to single (but NOT at start of line for indentation)
        text = re.sub(r"(?<=\S) {2,}", " ", text)
        return text

    def _strip_lines(self, text: str) -> str:
        """Strip trailing whitespace from each line."""
        lines = text.split("\n")
        return "\n".join(line.rstrip() for line in lines)


# ── Singleton instance ───────────────────────────────────────
text_cleaner = TextCleaner()
