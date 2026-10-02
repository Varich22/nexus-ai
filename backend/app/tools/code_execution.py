"""Code execution tool — runs Python in a sandboxed subprocess."""
from __future__ import annotations

import asyncio
import os
import resource
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

from app.core.config import Settings
from app.core.logging import get_logger
from app.tools.base import Tool

logger = get_logger(__name__)


class RunPythonTool(Tool):
    """Execute Python code in a sandboxed subprocess."""

    name = "run_python"
    description = (
        "Run a snippet of Python code and return stdout + stderr. Use this for "
        "calculations, data analysis, quick scripts, or to verify code logic. "
        "Has a timeout (default 10s) and output size limit. State does NOT "
        "persist between calls — each invocation is a fresh process."
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The Python code to execute.",
            },
        },
        "required": ["code"],
    }

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def run(self, code: str) -> str:
        timeout = self.settings.code_exec_timeout_seconds
        max_output = self.settings.code_exec_max_output_bytes

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"},
            )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return f"Error: execution timed out after {timeout}s"

            out = stdout.decode("utf-8", errors="replace")
            err = stderr.decode("utf-8", errors="replace")

            if len(out) > max_output:
                out = out[:max_output] + f"\n[... truncated, {len(out) - max_output} more chars]"
            if len(err) > max_output:
                err = err[:max_output] + f"\n[... truncated, {len(err) - max_output} more chars]"

            parts = []
            if out:
                parts.append(f"--- stdout ---\n{out}")
            if err:
                parts.append(f"--- stderr ---\n{err}")
            parts.append(f"--- exit code: {proc.returncode} ---")

            return "\n".join(parts) if parts else "(no output)"
        finally:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:  # noqa: BLE001
                pass
