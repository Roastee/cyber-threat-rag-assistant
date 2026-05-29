"""
Collection manager — CRUD operations on ChromaDB collections.

Wraps the ChromaService client to provide high-level collection
management: create, load, delete, add vectors, get stats, and
remove vectors by document ID.

Architecture:
    ┌─────────────────────────────────────────────┐
    │  CollectionManager  (this module)            │
    │  • get_or_create_collection()                │
    │  • add_documents()                           │
    │  • get_collection_stats()                    │
    │  • delete_by_doc_id()                        │
    │  • delete_collection()                       │
    └──────────────┬──────────────────────────────┘
                   │ uses
                   ▼
    ┌─────────────────────────────────────────────┐
    │  ChromaService  (chroma_service.py)          │
    │  • PersistentClient                          │
    └─────────────────────────────────────────────┘

Design Decision — Why not call ChromaDB directly?
    1. Testability: Mock CollectionManager, not the chromadb library
    2. Abstraction: If we switch to Pinecone, change this + chroma_service
    3. Metadata enrichment: We add `indexed_at` before storing
    4. Duplicate handling: We check if chunk_id exists before adding
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from src.vectorstore.chroma_service import (
    ChromaService,
    ChromaDBError,
    chroma_service,
    DEFAULT_COLLECTION_NAME,
)
from src.vectorstore.models import CollectionStats, VectorStoreInfo

logger = logging.getLogger(__name__)


class CollectionManager:
    """Manages ChromaDB collections with high-level CRUD operations.

    Usage:
        manager = CollectionManager()
        collection = manager.get_or_create_collection()
        manager.add_documents(ids, embeddings, documents, metadatas)
        stats = manager.get_collection_stats()
    """

    def __init__(
        self,
        service: ChromaService | None = None,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ) -> None:
        self._service = service or chroma_service
        self._collection_name = collection_name
        self._collection: Any = None

    @property
    def collection_name(self) -> str:
        return self._collection_name

    # ── Collection Lifecycle ─────────────────────────────────

    def get_or_create_collection(self) -> Any:
        """Get the collection, creating it if it doesn't exist.

        Uses cosine distance (matches our L2-normalized embeddings
        from sentence-transformers — cosine similarity = dot product
        for normalized vectors).
        """
        if self._collection is not None:
            return self._collection

        try:
            self._collection = self._service.client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            count = self._collection.count()
            logger.info(
                "Collection '%s' ready (%d vectors)",
                self._collection_name,
                count,
            )
            return self._collection

        except Exception as e:
            raise ChromaDBError(
                f"Failed to get/create collection '{self._collection_name}': {e}"
            ) from e

    def delete_collection(self) -> bool:
        """Delete the collection and all its data.

        Returns True if deleted, False if not found.
        """
        try:
            self._service.client.delete_collection(name=self._collection_name)
            self._collection = None
            logger.info("Deleted collection: %s", self._collection_name)
            return True
        except Exception as e:
            logger.warning("Failed to delete collection '%s': %s", self._collection_name, e)
            return False

    # ── Document Operations ──────────────────────────────────

    def add_documents(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> int:
        """Add documents with embeddings and metadata to the collection.

        Handles duplicates by checking existing IDs first and
        enriches metadata with an `indexed_at` timestamp.

        Args:
            ids:        Unique IDs for each document (chunk_id).
            embeddings: Pre-computed embedding vectors.
            documents:  Raw text content for each chunk.
            metadatas:  Metadata dicts for each chunk.

        Returns:
            Number of documents actually added (excludes duplicates).
        """
        collection = self.get_or_create_collection()

        if not ids:
            return 0

        # Check for existing IDs to avoid duplicates
        existing_ids = set()
        try:
            existing = collection.get(ids=ids, include=[])
            existing_ids = set(existing["ids"])
        except Exception:
            pass  # Collection might be empty or IDs not found

        # Filter out already-indexed chunks
        new_indices = [i for i, id_ in enumerate(ids) if id_ not in existing_ids]

        if not new_indices:
            logger.info("All %d chunks already indexed, skipping", len(ids))
            return 0

        # Prepare filtered data
        now = datetime.now(timezone.utc).isoformat()
        new_ids = [ids[i] for i in new_indices]
        new_embeddings = [embeddings[i] for i in new_indices]
        new_documents = [documents[i] for i in new_indices]
        new_metadatas = []
        for i in new_indices:
            meta = dict(metadatas[i])  # Copy to avoid mutating original
            meta["indexed_at"] = now
            new_metadatas.append(meta)

        # Add to collection
        try:
            collection.add(
                ids=new_ids,
                embeddings=new_embeddings,
                documents=new_documents,
                metadatas=new_metadatas,
            )
            logger.info(
                "Added %d vectors to '%s' (skipped %d duplicates)",
                len(new_ids),
                self._collection_name,
                len(ids) - len(new_ids),
            )
            return len(new_ids)

        except Exception as e:
            raise ChromaDBError(f"Failed to add documents: {e}") from e

    def delete_by_doc_id(self, doc_id: str) -> int:
        """Delete all vectors belonging to a specific document.

        Args:
            doc_id: The document ID whose vectors should be removed.

        Returns:
            Number of vectors deleted.
        """
        collection = self.get_or_create_collection()

        try:
            # First, get the IDs that match this doc_id
            results = collection.get(
                where={"doc_id": doc_id},
                include=[],
            )
            matching_ids = results["ids"]

            if not matching_ids:
                logger.info("No vectors found for doc_id=%s", doc_id)
                return 0

            # Delete them
            collection.delete(ids=matching_ids)
            logger.info(
                "Deleted %d vectors for doc_id=%s from '%s'",
                len(matching_ids),
                doc_id,
                self._collection_name,
            )
            return len(matching_ids)

        except Exception as e:
            logger.error("Failed to delete vectors for doc_id=%s: %s", doc_id, e)
            return 0

    # ── Statistics ────────────────────────────────────────────

    def get_collection_stats(self) -> CollectionStats:
        """Get statistics about the current collection."""
        try:
            collection = self.get_or_create_collection()
            count = collection.count()

            # Get unique doc_ids from metadata
            doc_ids: list[str] = []
            metadata_keys: list[str] = []
            dimensions = 0

            if count > 0:
                # Sample to get metadata keys and a vector for dimensions
                sample = collection.peek(limit=1)
                sample_meta = sample.get("metadatas")
                sample_emb = sample.get("embeddings")
                if sample_meta and len(sample_meta) > 0:
                    metadata_keys = list(sample_meta[0].keys())
                if sample_emb is not None and len(sample_emb) > 0:
                    dimensions = len(sample_emb[0])

                # Get all unique doc_ids
                all_meta = collection.get(include=["metadatas"])
                meta_list = all_meta.get("metadatas")
                if meta_list and len(meta_list) > 0:
                    doc_ids = list({
                        m.get("doc_id", "unknown")
                        for m in meta_list
                        if m
                    })

            return CollectionStats(
                name=self._collection_name,
                total_vectors=count,
                dimensions=dimensions,
                doc_ids=sorted(doc_ids),
                doc_count=len(doc_ids),
                metadata_keys=sorted(metadata_keys),
            )

        except Exception as e:
            logger.error("Failed to get collection stats: %s", e)
            return CollectionStats(name=self._collection_name)

    def get_store_info(self) -> VectorStoreInfo:
        """Get high-level info about the entire vector store."""
        try:
            collections = self._service.list_collections()
            total = 0
            for coll_name in collections:
                try:
                    coll = self._service.client.get_collection(name=coll_name)
                    total += coll.count()
                except Exception:
                    pass

            return VectorStoreInfo(
                persist_directory=self._service.persist_directory,
                collections=collections,
                total_vectors=total,
                is_persistent=True,
            )
        except Exception as e:
            logger.error("Failed to get store info: %s", e)
            return VectorStoreInfo(
                persist_directory=self._service.persist_directory,
            )


# ── Singleton ────────────────────────────────────────────────

collection_manager = CollectionManager()
