"""ChromaDB vector store — embeddings + persistence + retrieval."""
from __future__ import annotations

import uuid
from typing import Any

import chromadb

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client = None
_collection = None
COLLECTION_NAME = "nexus_memory"


def get_vector_store():
    """Get the global VectorStore singleton."""
    global _client, _collection
    if _collection is None:
        init_vector_store_sync()
    return _VectorStoreProxy()


async def init_vector_store() -> None:
    """Initialize ChromaDB at startup."""
    init_vector_store_sync()


def init_vector_store_sync() -> None:
    """Synchronous Chroma init."""
    global _client, _collection
    settings = get_settings()
    _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info("chromadb_ready", path=settings.chroma_persist_dir, items=_collection.count())


class _VectorStoreProxy:
    """Thin async-friendly facade over the Chroma collection."""

    async def add(self, text: str, metadata: dict | None = None) -> str:
        if _collection is None:
            raise RuntimeError("Vector store not initialized")
        item_id = str(uuid.uuid4())
        _collection.add(documents=[text], metadatas=[metadata or {}], ids=[item_id])
        return item_id

    async def query(self, query: str, k: int = 5, where: dict | None = None) -> list[dict]:
        if _collection is None:
            raise RuntimeError("Vector store not initialized")
        result = _collection.query(query_texts=[query], n_results=k, where=where)
        out: list[dict] = []
        for i, doc in enumerate(result.get("documents", [[]])[0]):
            meta = result.get("metadatas", [[]])[0][i] if result.get("metadatas") else {}
            dist = result.get("distances", [[]])[0][i] if result.get("distances") else None
            out.append({"text": doc, "metadata": meta, "distance": dist})
        return out

    async def delete_where(self, where: dict[str, Any]) -> bool:
        if _collection is None:
            return False
        try:
            _collection.delete(where=where)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("chroma_delete_failed", error=str(exc))
            return False

    async def count(self) -> int:
        if _collection is None:
            return 0
        return _collection.count()
