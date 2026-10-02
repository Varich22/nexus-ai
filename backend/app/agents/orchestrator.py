"""Agent orchestrator — the heart of the system.

Receives user input, manages conversation context, calls the LLM via LiteLLM,
invokes tools when needed, loops until a final answer is produced, and streams
tokens back to the caller.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, AsyncIterator

from litellm import acompletion

from app.agents.prompts import DEFAULT_SYSTEM_PROMPT
from app.core.config import Settings
from app.core.logging import get_logger
from app.models.schemas import ChatMessage, MessageRole, ToolCall
from app.tools.base import Tool
from app.tools.code_execution import RunPythonTool
from app.tools.file_ops import EditFileTool, ListDirTool, ReadFileTool, WriteFileTool
from app.tools.registry import ToolRegistry
from app.tools.web_fetch import WebFetchTool
from app.tools.web_search import WebSearchTool

logger = get_logger(__name__)


class AgentOrchestrator:
    """Orchestrates the LLM ↔ tool loop for a single conversation."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.tools = ToolRegistry()
        self._register_default_tools()
        self._conversations: dict[str, list[ChatMessage]] = {}

    # ------------------------------------------------------------------ tools

    def _register_default_tools(self) -> None:
        """Register the default toolset."""
        defaults: list[Tool] = [
            WebSearchTool(self.settings),
            WebFetchTool(),
            ReadFileTool(),
            WriteFileTool(),
            EditFileTool(),
            ListDirTool(),
            RunPythonTool(self.settings),
        ]
        for tool in defaults:
            self.tools.register(tool)

    # -------------------------------------------------------- conversation IO

    def get_history(self, conversation_id: str) -> list[ChatMessage]:
        return self._conversations.get(conversation_id, [])

    def append_message(self, conversation_id: str, message: ChatMessage) -> None:
        self._conversations.setdefault(conversation_id, []).append(message)

    def clear_conversation(self, conversation_id: str) -> bool:
        return self._conversations.pop(conversation_id, None) is not None

    # -------------------------------------------------------------- main run

    async def run(
        self,
        conversation_id: str,
        user_message: str,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Run the agent until a final response is produced. Returns the full result."""
        system = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.append_message(
            conversation_id,
            ChatMessage(
                id=str(uuid.uuid4()),
                role=MessageRole.USER,
                content=user_message,
            ),
        )

        tool_calls_log: list[dict] = []
        iterations = 0

        while iterations < self.settings.max_agent_iterations:
            iterations += 1
            messages = self._build_messages(conversation_id, system)

            response = await acompletion(
                model=self.settings.llm_model,
                messages=messages,
                tools=self.tools.to_openai_tools(),
                tool_choice="auto",
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.llm_max_tokens,
                api_key=self.settings.openai_api_key,
                stream=False,
            )

            choice = response.choices[0]
            assistant_message = choice.message

            # Case 1: tool call(s) requested
            if assistant_message.tool_calls:
                tool_messages = []
                for tc in assistant_message.tool_calls:
                    tool = self.tools.get(tc.function.name)
                    args = self._safe_parse_args(tc.function.arguments)
                    logger.info(
                        "tool_call",
                        tool=tc.function.name,
                        args=args,
                        iteration=iterations,
                    )

                    if tool is None:
                        result = f"Error: unknown tool '{tc.function.name}'"
                        error = "unknown_tool"
                    else:
                        try:
                            result = await tool.run(**args)
                            error = None
                        except Exception as exc:  # noqa: BLE001
                            logger.exception("tool_failed", tool=tc.function.name)
                            result = f"Error: {exc}"
                            error = str(exc)

                    tool_call = ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args,
                        result=result,
                        error=error,
                    )
                    tool_calls_log.append(tool_call.model_dump())

                    tool_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": tc.function.name,
                            "content": result,
                        }
                    )

                # Append the assistant message (with tool_calls) so the LLM has context
                self.append_message(
                    conversation_id,
                    ChatMessage(
                        id=str(uuid.uuid4()),
                        role=MessageRole.ASSISTANT,
                        content=assistant_message.content or "",
                        tool_calls=[
                            ToolCall(
                                id=tc.id,
                                name=tc.function.name,
                                arguments=self._safe_parse_args(tc.function.arguments),
                            )
                            for tc in assistant_message.tool_calls
                        ],
                    ),
                )

                # Continue the loop with tool results
                messages.extend(self._convert_to_openai(self._conversations[conversation_id]))
                messages.extend(tool_messages)
                continue

            # Case 2: final response
            final_content = assistant_message.content or ""
            message_id = str(uuid.uuid4())
            self.append_message(
                conversation_id,
                ChatMessage(
                    id=message_id,
                    role=MessageRole.ASSISTANT,
                    content=final_content,
                ),
            )
            return {
                "conversation_id": conversation_id,
                "message_id": message_id,
                "content": final_content,
                "tool_calls": tool_calls_log,
                "iterations": iterations,
            }

        # Hit iteration cap
        logger.warning("max_iterations_reached", conversation_id=conversation_id)
        message_id = str(uuid.uuid4())
        fallback = (
            "J'ai atteint la limite d'itérations sans produire de réponse finale. "
            "Peux-tu reformuler ou découper ta question ?"
        )
        self.append_message(
            conversation_id,
            ChatMessage(id=message_id, role=MessageRole.ASSISTANT, content=fallback),
        )
        return {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "content": fallback,
            "tool_calls": tool_calls_log,
            "iterations": iterations,
        }

    # ----------------------------------------------------------- streaming run

    async def stream(
        self,
        conversation_id: str,
        user_message: str,
        system_prompt: str | None = None,
    ) -> AsyncIterator[dict]:
        """Streaming version: yields SSE events as the agent runs.

        Event types: 'start', 'token', 'tool_call', 'tool_result', 'done', 'error'.
        """
        try:
            yield {
                "type": "start",
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # For simplicity in v1, do non-streaming tool-calling but stream final tokens.
            result = await self.run(conversation_id, user_message, system_prompt)

            for tc in result.get("tool_calls", []):
                yield {
                    "type": "tool_call",
                    "name": tc.get("name"),
                    "arguments": tc.get("arguments"),
                }
                yield {
                    "type": "tool_result",
                    "name": tc.get("name"),
                    "result": (tc.get("result") or "")[:500],
                    "error": tc.get("error"),
                }

            # Stream the final content in chunks (simulated, for UX consistency)
            content = result.get("content", "")
            chunk_size = 20
            for i in range(0, len(content), chunk_size):
                yield {
                    "type": "token",
                    "content": content[i : i + chunk_size],
                }

            yield {
                "type": "done",
                "message_id": result.get("message_id"),
                "iterations": result.get("iterations", 0),
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception("stream_error", error=str(exc))
            yield {"type": "error", "message": str(exc)}

    # ---------------------------------------------------------------- helpers

    def _build_messages(self, conversation_id: str, system: str) -> list[dict]:
        messages: list[dict] = [{"role": "system", "content": system}]
        messages.extend(self._convert_to_openai(self._conversations.get(conversation_id, [])))
        return messages

    @staticmethod
    def _convert_to_openai(messages: list[ChatMessage]) -> list[dict]:
        out: list[dict] = []
        for m in messages:
            if m.role == MessageRole.TOOL:
                continue  # handled separately in tool loop
            entry: dict = {"role": m.role.value, "content": m.content}
            if m.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in m.tool_calls
                ]
            out.append(entry)
        return out

    @staticmethod
    def _safe_parse_args(raw: str | dict) -> dict:
        if isinstance(raw, dict):
            return raw
        try:
            return json.loads(raw or "{}")
        except json.JSONDecodeError:
            return {}
