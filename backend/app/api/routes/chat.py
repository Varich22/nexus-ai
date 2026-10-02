"""Chat endpoints — streaming and non-streaming."""
from __future__ import annotations

import json
import uuid
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agents.orchestrator import AgentOrchestrator
from app.api.deps import verify_api_key
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.models.schemas import ChatMessage, MessageRole

logger = get_logger(__name__)

router = APIRouter(dependencies=[Depends(verify_api_key)])


class ChatRequest(BaseModel):
    """Chat request body."""

    message: str = Field(..., min_length=1, max_length=32000, description="User message")
    conversation_id: str | None = Field(
        default=None, description="Existing conversation ID; new one if omitted"
    )
    stream: bool = Field(default=False, description="Enable SSE streaming")
    system_prompt: str | None = Field(default=None, description="Override system prompt")


class ChatResponse(BaseModel):
    """Non-streaming chat response."""

    conversation_id: str
    message_id: str
    content: str
    tool_calls: list[dict] = Field(default_factory=list)
    iterations: int = 0


@router.post("/chat", response_model=None)
async def chat(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
) -> StreamingResponse | ChatResponse:
    """Send a message to the agent.

    If `stream=true`, returns a Server-Sent Events stream.
    Otherwise returns the full response.
    """
    orchestrator = AgentOrchestrator(settings)
    conversation_id = request.conversation_id or str(uuid.uuid4())

    if request.stream:
        return StreamingResponse(
            _stream_chat(orchestrator, conversation_id, request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "X-Conversation-Id": conversation_id,
            },
        )

    # Non-streaming path
    try:
        result = await orchestrator.run(
            conversation_id=conversation_id,
            user_message=request.message,
            system_prompt=request.system_prompt,
        )
    except Exception as exc:
        logger.exception("chat_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent run failed: {exc}",
        ) from exc

    return ChatResponse(
        conversation_id=result["conversation_id"],
        message_id=result["message_id"],
        content=result["content"],
        tool_calls=result.get("tool_calls", []),
        iterations=result.get("iterations", 0),
    )


async def _stream_chat(
    orchestrator: AgentOrchestrator,
    conversation_id: str,
    request: ChatRequest,
) -> AsyncIterator[str]:
    """Yield SSE-formatted chunks from the agent run."""
    try:
        async for event in orchestrator.stream(
            conversation_id=conversation_id,
            user_message=request.message,
            system_prompt=request.system_prompt,
        ):
            yield f"data: {json.dumps(event, default=str)}\n\n"
    except Exception as exc:  # noqa: BLE001
        logger.exception("stream_failed", error=str(exc))
        err = {"type": "error", "message": str(exc)}
        yield f"data: {json.dumps(err)}\n\n"
    finally:
        yield "data: [DONE]\n\n"


@router.get("/chat/tools")
async def list_tools(settings: Settings = Depends(get_settings)) -> dict:
    """List all available tools (name, description, parameters)."""
    orchestrator = AgentOrchestrator(settings)
    return {
        "tools": [t.to_openai_schema() for t in orchestrator.tools.list_tools()],
        "count": len(orchestrator.tools.list_tools()),
    }
