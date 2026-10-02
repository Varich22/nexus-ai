"""Web search tool — Tavily (preferred) or DuckDuckGo fallback."""
from __future__ import annotations

import asyncio

import httpx

from app.core.config import Settings
from app.core.logging import get_logger
from app.tools.base import Tool

logger = get_logger(__name__)


class WebSearchTool(Tool):
    """Search the web and return summarized results with sources."""

    name = "web_search"
    description = (
        "Search the web for current information. Use this whenever the user asks "
        "about real-world facts, recent events, prices, news, or anything that "
        "requires up-to-date information. Returns a list of results with title, "
        "snippet, and URL."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query. Be specific and concise.",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results (1-10).",
                "default": 5,
                "minimum": 1,
                "maximum": 10,
            },
        },
        "required": ["query"],
    }

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def run(self, query: str, max_results: int = 5) -> str:
        """Execute web search via Tavily if available, else DuckDuckGo fallback."""
        if self.settings.tavily_api_key:
            return await self._search_tavily(query, max_results)
        return await self._search_duckduckgo(query, max_results)

    async def _search_tavily(self, query: str, max_results: int) -> str:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.settings.tavily_api_key,
                        "query": query,
                        "max_results": max_results,
                        "search_depth": "basic",
                        "include_answer": True,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            logger.warning("tavily_failed", error=str(exc))
            return await self._search_duckduckgo(query, max_results)

        results = data.get("results", [])
        answer = data.get("answer")
        lines: list[str] = []
        if answer:
            lines.append(f"Answer: {answer}\n")
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r.get('title', '')}\n   {r.get('url', '')}\n   {r.get('content', '')[:300]}")
        return "\n".join(lines) if lines else "No results found."

    async def _search_duckduckgo(self, query: str, max_results: int) -> str:
        """DuckDuckGo fallback — uses the lite HTML endpoint."""
        try:
            async with httpx.AsyncClient(
                timeout=15.0,
                headers={"User-Agent": "nexus-ai/0.1 (research tool)"},
                follow_redirects=True,
            ) as client:
                resp = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                )
                resp.raise_for_status()
                html = resp.text
        except httpx.HTTPError as exc:
            return f"Web search failed: {exc}"

        # Naive HTML parsing — no external deps
        results: list[str] = []
        for chunk in html.split('class="result__a"')[1 : max_results + 1]:
            try:
                link_end = chunk.find('"')
                href_start = chunk.find('href="')
                href = ""
                if href_start != -1:
                    href_end = chunk.find('"', href_start + 6)
                    href = chunk[href_start + 6 : href_end]
                title_end = chunk.find("</a>")
                title_html = chunk[link_end:title_end] if title_end != -1 else ""
                # Strip tags
                import re

                title = re.sub(r"<[^>]+>", "", title_html).strip()

                # Snippet
                snippet_marker = 'class="result__snippet"'
                snippet_idx = html.find(snippet_marker, html.find(chunk))
                snippet = ""
                if snippet_idx != -1:
                    snip_start = snippet_idx + len(snippet_marker)
                    snip_end = html.find("</a>", snip_start)
                    snip_html = html[snip_start:snip_end]
                    snippet = re.sub(r"<[^>]+>", "", snip_html).strip()[:300]

                results.append(f"- {title}\n  {href}\n  {snippet}")
            except Exception:  # noqa: BLE001
                continue

        return "\n\n".join(results) if results else "No results found."
