"""Tests for individual tools."""
from __future__ import annotations

import pytest

from app.tools.file_ops import ListDirTool, ReadFileTool, WriteFileTool
from app.tools.web_fetch import WebFetchTool


@pytest.mark.asyncio
async def test_write_then_read_file(tmp_path) -> None:
    """write_file then read_file round-trips content."""
    target = tmp_path / "hello.txt"
    writer = WriteFileTool()
    reader = ReadFileTool()

    out = await writer.run(path=str(target), content="hello world")
    assert "Written" in out

    out = await reader.run(path=str(target))
    assert "hello world" in out
    assert "hello.txt" in out


@pytest.mark.asyncio
async def test_read_missing_file() -> None:
    """read_file on a missing file should report the error clearly."""
    reader = ReadFileTool()
    out = await reader.run(path="/nonexistent/path/abc.xyz")
    assert "not found" in out.lower()


@pytest.mark.asyncio
async def test_list_dir(tmp_path) -> None:
    """list_dir should return entries in a directory."""
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b").mkdir()
    lister = ListDirTool()
    out = await lister.run(path=str(tmp_path))
    assert "a.txt" in out
    assert "b" in out


@pytest.mark.asyncio
async def test_web_fetch_rejects_bad_url() -> None:
    """web_fetch should reject non-http URLs."""
    fetcher = WebFetchTool()
    out = await fetcher.run(url="not-a-url")
    assert "Invalid URL" in out
