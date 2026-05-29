"""
Embedding service — generates vector embeddings from text.

This is the **abstraction layer** that isolates the rest of the system
from the specific embedding model. All other code calls EmbeddingService
methods; none of it imports sentence_transformers directly.

Architecture — Provider Pattern:
    ┌──────────────────────────────────────┐
    │  EmbeddingService (public API)       │
    │  • embed_text(str) → list[float]     │
    │  • embed_batch(list[str]) → vectors  │
    │  • model_name, dimensions            │
    └────────────┬─────────────────────────┘
                 │ delegates to
                 ▼
    ┌──────────────────────────────────────┐
    │  SentenceTransformer                 │
    │  (or future: OpenAI, Cohere, etc.)   │
    └──────────────────────────────────────┘

    To swap models, change DEFAULT_MODEL_NAME or create a new service
    class implementing the same interface. No other file changes needed.

Design Decision — Lazy Loading:
    The SentenceTransformer model is ~80 MB. We load it lazily (on first
    embed call) so that importing this module doesn't block app startup.
    The model is then cached as a singleton for the process lifetime.
"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────

DEFAULT_MODEL_NAME: str = "all-MiniLM-L6-v2"
DEFAULT_BATCH_SIZE: int = 32


class EmbeddingService:
    """Generates vector embeddings using sentence-transformers.

    This is the only class in the system that imports sentence_transformers.
    All other modules interact with embeddings through this interface.

    Usage:
        service = EmbeddingService()                     # lazy load
        vector = service.embed_text("APT29 attack")      # single text
        vectors = service.embed_batch(["text1", "text2"]) # batch

    Model swapping:
        service = EmbeddingService(model_name="all-mpnet-base-v2")
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        self._model_name = model_name
        self._batch_size = batch_size
        self._model: Any = None  # Lazy-loaded SentenceTransformer
        self._dimensions: int = 0

    # ── Properties ───────────────────────────────────────────

    @property
    def model_name(self) -> str:
        """Name of the embedding model."""
        return self._model_name

    @property
    def dimensions(self) -> int:
        """Dimensionality of the embedding vectors.

        Returns 0 if the model hasn't been loaded yet.
        After first embed call, returns the actual dimension count.
        """
        return self._dimensions

    @property
    def batch_size(self) -> int:
        """Batch size used for encoding."""
        return self._batch_size

    @property
    def is_loaded(self) -> bool:
        """Whether the model is currently loaded in memory."""
        return self._model is not None

    # ── Core Methods ─────────────────────────────────────────

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string into a vector.

        Args:
            text: The input text to embed.

        Returns:
            A list of floats representing the embedding vector.

        Raises:
            EmbeddingError: If embedding fails.
        """
        if not text or not text.strip():
            raise EmbeddingError("Cannot embed empty text.")

        model = self._ensure_model_loaded()

        try:
            vector = model.encode(
                text,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            return vector.tolist()
        except Exception as e:
            raise EmbeddingError(f"Failed to embed text: {e}") from e

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts in an optimized batch.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (same order as input texts).

        Raises:
            EmbeddingError: If embedding fails.
        """
        if not texts:
            return []

        # Filter out empty strings but track their indices
        valid_indices = [i for i, t in enumerate(texts) if t and t.strip()]
        valid_texts = [texts[i] for i in valid_indices]

        if not valid_texts:
            raise EmbeddingError("All texts in the batch are empty.")

        model = self._ensure_model_loaded()

        try:
            start_time = time.perf_counter()

            vectors = model.encode(
                valid_texts,
                batch_size=self._batch_size,
                show_progress_bar=False,
                normalize_embeddings=True,
            )

            elapsed = time.perf_counter() - start_time
            logger.info(
                "Embedded %d texts in %.2fs (%.1f texts/sec, model=%s)",
                len(valid_texts),
                elapsed,
                len(valid_texts) / elapsed if elapsed > 0 else 0,
                self._model_name,
            )

            # Convert numpy arrays to Python lists
            result_vectors = vectors.tolist()

            # If some texts were empty, insert zero vectors at their positions
            if len(valid_indices) < len(texts):
                full_results: list[list[float]] = []
                valid_iter = iter(result_vectors)
                for i in range(len(texts)):
                    if i in valid_indices:
                        full_results.append(next(valid_iter))
                    else:
                        full_results.append([0.0] * self._dimensions)
                return full_results

            return result_vectors

        except Exception as e:
            raise EmbeddingError(f"Batch embedding failed: {e}") from e

    # ── Model Management ─────────────────────────────────────

    def _ensure_model_loaded(self) -> Any:
        """Lazy-load the SentenceTransformer model.

        First call downloads the model (~80 MB) and caches it.
        Subsequent calls return the cached instance.
        """
        if self._model is not None:
            return self._model

        logger.info("Loading embedding model: %s ...", self._model_name)
        start_time = time.perf_counter()

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
            # Discover dimensions from the model config
            self._dimensions = self._model.get_embedding_dimension()

            elapsed = time.perf_counter() - start_time
            logger.info(
                "Model loaded: %s (%d dimensions, %.2fs)",
                self._model_name,
                self._dimensions,
                elapsed,
            )

            return self._model

        except ImportError as e:
            raise EmbeddingError(
                "sentence-transformers is not installed. "
                "Run: pip install sentence-transformers"
            ) from e
        except Exception as e:
            raise EmbeddingError(
                f"Failed to load model '{self._model_name}': {e}"
            ) from e

    def unload_model(self) -> None:
        """Release the model from memory."""
        if self._model is not None:
            logger.info("Unloading model: %s", self._model_name)
            self._model = None
            self._dimensions = 0

    def get_info(self) -> dict[str, Any]:
        """Return model information for display."""
        return {
            "model_name": self._model_name,
            "dimensions": self._dimensions,
            "batch_size": self._batch_size,
            "is_loaded": self.is_loaded,
        }


# ── Exceptions ───────────────────────────────────────────────


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""


# ── Singleton ────────────────────────────────────────────────

embedding_service = EmbeddingService()
