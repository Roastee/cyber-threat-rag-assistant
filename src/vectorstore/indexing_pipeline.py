"""
Indexing pipeline — orchestrates Chunks + Embeddings → ChromaDB.

Takes processed chunks and their corresponding embedding records,
maps them to ChromaDB's add() interface, and indexes them into
the persistent collection.

Data flow:
    Chunks + EmbeddingRecords
        │
        ├─ Extract: ids (chunk_id), documents (content),
        │           embeddings (vector), metadatas (chunk.metadata)
        │
        ├─ CollectionManager.add_documents()
        │   └─ Duplicate check → metadata enrichment → ChromaDB add
        │
        └─→ IndexingResult (counts + timing)

Design Decision — Why a pipeline on top of CollectionManager?
    CollectionManager is generic (accepts raw ids/embeddings/documents).
    The indexing pipeline is application-specific: it knows about
    Chunk and EmbeddingRecord objects, handles the mapping, and
    computes indexing statistics for the UI.
"""

from __future__ import annotations

import logging
import time

from src.models.chunk import Chunk
from src.embeddings.models import EmbeddingRecord
from src.vectorstore.collection_manager import CollectionManager, collection_manager
from src.vectorstore.chroma_service import ChromaDBError
from src.vectorstore.models import IndexingResult

logger = logging.getLogger(__name__)


class IndexingPipeline:
    """Orchestrates chunk + embedding → ChromaDB indexing.

    Usage:
        pipeline = IndexingPipeline()
        result = pipeline.index_document(chunks, records, doc_id="abc")
        if result.success:
            print(f"Indexed {result.indexed_count} vectors")
    """

    def __init__(self, manager: CollectionManager | None = None) -> None:
        self._manager = manager or collection_manager

    def index_document(
        self,
        chunks: list[Chunk],
        embedding_records: list[EmbeddingRecord],
        doc_id: str = "",
    ) -> IndexingResult:
        """Index a document's chunks and embeddings into ChromaDB.

        Args:
            chunks:            Chunk objects with text and metadata.
            embedding_records: Corresponding embedding vectors.
            doc_id:            Parent document ID.

        Returns:
            IndexingResult with success status and counts.
        """
        if not chunks or not embedding_records:
            return IndexingResult(
                success=False,
                doc_id=doc_id,
                error="No chunks or embeddings provided for indexing.",
            )

        if len(chunks) != len(embedding_records):
            return IndexingResult(
                success=False,
                doc_id=doc_id,
                error=(
                    f"Chunk count ({len(chunks)}) does not match "
                    f"embedding count ({len(embedding_records)})"
                ),
            )

        logger.info(
            "Indexing %d chunks for doc_id=%s into '%s'",
            len(chunks),
            doc_id,
            self._manager.collection_name,
        )

        start_time = time.perf_counter()

        try:
            # Build the parallel arrays ChromaDB expects
            ids: list[str] = []
            embeddings: list[list[float]] = []
            documents: list[str] = []
            metadatas: list[dict] = []

            # Create a lookup from chunk_id → embedding vector
            embedding_map = {rec.chunk_id: rec.vector for rec in embedding_records}

            for chunk in chunks:
                vector = embedding_map.get(chunk.chunk_id)
                if vector is None:
                    logger.warning(
                        "No embedding found for chunk_id=%s, skipping",
                        chunk.chunk_id,
                    )
                    continue

                ids.append(chunk.chunk_id)
                embeddings.append(vector)
                documents.append(chunk.content)
                metadatas.append(chunk.metadata)

            if not ids:
                return IndexingResult(
                    success=False,
                    doc_id=doc_id,
                    error="No valid chunk-embedding pairs found.",
                )

            # Index into ChromaDB
            added_count = self._manager.add_documents(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )

            elapsed = time.perf_counter() - start_time
            skipped = len(ids) - added_count

            logger.info(
                "Indexed doc_id=%s: %d added, %d skipped, %.3fs",
                doc_id,
                added_count,
                skipped,
                elapsed,
            )

            return IndexingResult(
                success=True,
                indexed_count=added_count,
                skipped_count=skipped,
                doc_id=doc_id,
                collection_name=self._manager.collection_name,
                time_secs=elapsed,
            )

        except ChromaDBError as e:
            logger.error("Indexing failed for doc_id=%s: %s", doc_id, e)
            return IndexingResult(
                success=False,
                doc_id=doc_id,
                error=str(e),
            )
        except Exception as e:
            logger.error("Unexpected indexing error for doc_id=%s: %s", doc_id, e)
            return IndexingResult(
                success=False,
                doc_id=doc_id,
                error=f"Indexing failed: {e}",
            )

    def remove_document(self, doc_id: str) -> int:
        """Remove all indexed vectors for a document.

        Returns the number of vectors removed.
        """
        return self._manager.delete_by_doc_id(doc_id)


# ── Singleton ────────────────────────────────────────────────

indexing_pipeline = IndexingPipeline()
