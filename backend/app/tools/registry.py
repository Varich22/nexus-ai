"""Tool registry — manages available tools for the agent."""
from __future__ import annotations

from app.tools.base import Tool


class ToolRegistry:
    """Holds all available tools, supports lookup and OpenAI-format export."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool (overwrites if name conflicts)."""
        if not tool.name:
            raise ValueError("Tool must have a non-empty name")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """Look up a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        """Return all registered tools."""
        return list(self._tools.values())

    def to_openai_tools(self) -> list[dict]:
        """Export all tools in OpenAI function-calling format."""
        return [t.to_openai_schema() for t in self._tools.values()]

    def __len__(self) -> int:
        return len(self._tools)
