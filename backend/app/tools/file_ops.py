"""File operations tools — read, write, edit, list directory."""
from __future__ import annotations

import os
import re
from pathlib import Path

from app.tools.base import Tool


class ReadFileTool(Tool):
    """Read the contents of a file."""

    name = "read_file"
    description = (
        "Read the contents of a file on the local filesystem. Use this to access "
        "code, configs, documents, or any text file the user wants to discuss."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file (relative or absolute).",
            },
        },
        "required": ["path"],
    }

    async def run(self, path: str) -> str:
        try:
            p = Path(path).expanduser()
            if not p.exists():
                return f"Error: file not found: {path}"
            if not p.is_file():
                return f"Error: not a file: {path}"
            if p.stat().st_size > 1_000_000:
                return f"Error: file too large (>1MB): {path}"

            content = p.read_text(encoding="utf-8", errors="replace")
            return f"--- {path} ({len(content)} chars) ---\n{content}"
        except Exception as exc:  # noqa: BLE001
            return f"Error reading {path}: {exc}"


class WriteFileTool(Tool):
    """Write content to a file (creates or overwrites)."""

    name = "write_file"
    description = (
        "Write text content to a file, creating it or overwriting if it exists. "
        "Use this to create new files or fully replace existing ones."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to write.",
            },
            "content": {
                "type": "string",
                "description": "Full content to write to the file.",
            },
        },
        "required": ["path", "content"],
    }

    async def run(self, path: str, content: str) -> str:
        try:
            p = Path(path).expanduser()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return f"Written {len(content)} chars to {path}"
        except Exception as exc:  # noqa: BLE001
            return f"Error writing {path}: {exc}"


class EditFileTool(Tool):
    """Edit a file by finding and replacing a specific text block."""

    name = "edit_file"
    description = (
        "Edit a file by replacing a specific block of text. Use this for "
        "targeted edits rather than full rewrites. The 'old_text' must match "
        "exactly (including whitespace and indentation)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to edit.",
            },
            "old_text": {
                "type": "string",
                "description": "The exact text to find (must be unique in the file).",
            },
            "new_text": {
                "type": "string",
                "description": "The text to replace it with.",
            },
        },
        "required": ["path", "old_text", "new_text"],
    }

    async def run(self, path: str, old_text: str, new_text: str) -> str:
        try:
            p = Path(path).expanduser()
            if not p.exists():
                return f"Error: file not found: {path}"
            content = p.read_text(encoding="utf-8")

            occurrences = content.count(old_text)
            if occurrences == 0:
                return f"Error: old_text not found in {path}"
            if occurrences > 1:
                return f"Error: old_text matches {occurrences} locations — be more specific"

            new_content = content.replace(old_text, new_text, 1)
            p.write_text(new_content, encoding="utf-8")
            return f"Edited {path} ({len(new_text) - len(old_text):+d} chars)"
        except Exception as exc:  # noqa: BLE001
            return f"Error editing {path}: {exc}"


class ListDirTool(Tool):
    """List files in a directory."""

    name = "list_dir"
    description = (
        "List the contents of a directory. Returns file and folder names with "
        "their types. Use this to explore the filesystem structure."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path. Defaults to current directory if omitted.",
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum depth to traverse (1 = just immediate contents).",
                "default": 1,
                "minimum": 1,
                "maximum": 5,
            },
        },
        "required": [],
    }

    async def run(self, path: str = ".", max_depth: int = 1) -> str:
        try:
            p = Path(path).expanduser()
            if not p.exists():
                return f"Error: directory not found: {path}"
            if not p.is_dir():
                return f"Error: not a directory: {path}"

            lines: list[str] = [f"{p}/"]

            def _walk(current: Path, prefix: str, depth: int) -> None:
                if depth > max_depth:
                    return
                try:
                    entries = sorted(current.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
                except PermissionError:
                    lines.append(f"{prefix}[permission denied]")
                    return

                # Skip heavy / hidden
                entries = [e for e in entries if not e.name.startswith(".") and e.name not in {
                    "node_modules", "__pycache__", "venv", ".venv", "dist", "build",
                }]
                for entry in entries:
                    marker = "📁" if entry.is_dir() else "📄"
                    size = ""
                    if entry.is_file():
                        try:
                            s = entry.stat().st_size
                            size = f" ({s:,} B)"
                        except OSError:
                            pass
                    lines.append(f"{prefix}{marker} {entry.name}{size}")
                    if entry.is_dir() and depth < max_depth:
                        _walk(entry, prefix + "  ", depth + 1)

            _walk(p, "  ", 1)
            return "\n".join(lines)
        except Exception as exc:  # noqa: BLE001
            return f"Error listing {path}: {exc}"
