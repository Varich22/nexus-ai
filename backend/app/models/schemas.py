"""Pydantic models — API I/O and core domain objects."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of a message in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCall(BaseModel):
    """A tool invocation by the assistant."""

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: str | None = None
    error: str | None = None


class ChatMessage(BaseModel):
    """A single message in a conversation."""

    id: str
    role: MessageRole
    content: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Conversation(BaseModel):
    """A conversation thread."""

    id: str
    messages: list[ChatMessage] = Field(default_factory=list)
    system_prompt: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
