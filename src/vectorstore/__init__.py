"""
src.vectorstore — ChromaDB vector store integration.

Public API:
    - ChromaService / chroma_service:           Low-level ChromaDB client.
    - CollectionManager / collection_manager:   Collection CRUD + add/delete/stats.
    - IndexingPipeline / indexing_pipeline:      Chunks + Embeddings → ChromaDB.
    - IndexingResult:                            Result of an indexing operation.
    - CollectionStats:                           Collection statistics.
    - VectorStoreInfo:                           Store-wide info.
    - ChromaDBError:                             Exception type.
"""

from src.vectorstore.models import IndexingResult, CollectionStats, VectorStoreInfo
from src.vectorstore.chroma_service import (
    ChromaService,
    ChromaDBError,
    chroma_service,
    DEFAULT_COLLECTION_NAME,
    DEFAULT_PERSIST_DIR,
)
from src.vectorstore.collection_manager import (
    CollectionManager,
    collection_manager,
)
from src.vectorstore.indexing_pipeline import (
    IndexingPipeline,
    indexing_pipeline,
)

__all__ = [
    "ChromaService",
    "ChromaDBError",
    "chroma_service",
    "DEFAULT_COLLECTION_NAME",
    "DEFAULT_PERSIST_DIR",
    "CollectionManager",
    "collection_manager",
    "IndexingPipeline",
    "indexing_pipeline",
    "IndexingResult",
    "CollectionStats",
    "VectorStoreInfo",
]
