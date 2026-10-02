"""Tool base class — every tool extends this."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """Base class for agent tools.

    Each tool exposes:
    - name (str)
    - description (str) — shown to the LLM so it knows when to use the tool
    - parameters (dict) — JSON Schema for the tool's arguments
    - async run(**kwargs) — executes the tool

    Tools are auto-converted to OpenAI function-calling format by the registry.
    """

    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    @abstractmethod
    async def run(self, **kwargs: Any) -> str:
        """Execute the tool and return a string result."""
        raise NotImplementedError

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert to OpenAI function-calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
