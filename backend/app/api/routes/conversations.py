"""Conversation management endpoints (in-memory for v1)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import verify_api_key
from app.services.memory import MemoryService

router = APIRouter(dependencies=[Depends(verify_api_key)])


class ConversationSummary(BaseModel):
    """Summary of a stored conversation."""

    conversation_id: str
    message_count: int
    last_active: str


@router.get("/conversations")
async def list_conversations() -> dict:
    """List recent conversations (placeholder — wired in v2)."""
    # In v1 we keep history in-process; v2 will persist to SQL.
    return {"conversations": [], "total": 0, "note": "persistence arriving in v2"}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str) -> dict:
    """Delete a conversation and its memory."""
    svc = MemoryService()
    deleted = await svc.clear_conversation(conversation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return {"deleted": True, "conversation_id": conversation_id}
