"""Memory service — high-level interface over the vector store."""
from __future__ import annotations

from app.core.logging import get_logger
from app.memory.vector import get_vector_store

logger = get_logger(__name__)


class MemoryService:
    """Convenience facade for memory operations."""

    def __init__(self) -> None:
        self.store = get_vector_store()

    async def store_fact(self, conversation_id: str, fact: str, metadata: dict | None = None) -> str:
        """Store a fact/summary tied to a conversation."""
        meta = {"conversation_id": conversation_id, **(metadata or {})}
        return await self.store.add(text=fact, metadata=meta)

    async def search(self, query: str, k: int = 5, conversation_id: str | None = None) -> list[dict]:
        """Search the memory store for relevant past facts."""
        where = {"conversation_id": conversation_id} if conversation_id else None
        return await self.store.query(query=query, k=k, where=where)

    async def clear_conversation(self, conversation_id: str) -> bool:
        """Remove all memory entries for a conversation."""
        return await self.store.delete_where({"conversation_id": conversation_id})
