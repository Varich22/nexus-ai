"""Web fetch tool — retrieves and extracts text from a URL."""
from __future__ import annotations

import re

import httpx

from app.tools.base import Tool


class WebFetchTool(Tool):
    """Fetch a URL and extract its main text content."""

    name = "web_fetch"
    description = (
        "Fetch a web page and return its extracted text content. Use this when "
        "you need to read the contents of a specific URL found via web_search, "
        "or when the user provides a URL to analyze."
    )
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch (must be http:// or https://).",
            },
            "max_chars": {
                "type": "integer",
                "description": "Maximum number of characters to return.",
                "default": 8000,
                "minimum": 100,
                "maximum": 50000,
            },
        },
        "required": ["url"],
    }

    async def run(self, url: str, max_chars: int = 8000) -> str:
        if not url.startswith(("http://", "https://")):
            return f"Invalid URL: {url}"

        try:
            async with httpx.AsyncClient(
                timeout=20.0,
                follow_redirects=True,
                headers={"User-Agent": "nexus-ai/0.1 (research tool)"},
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "")
                body = resp.text
        except httpx.HTTPError as exc:
            return f"Fetch failed: {exc}"

        if "html" in content_type.lower():
            text = self._extract_text_from_html(body)
        else:
            text = body

        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n[... truncated, {len(text) - max_chars} more chars]"

        return f"URL: {url}\nContent-Type: {content_type}\n\n{text}"

    @staticmethod
    def _extract_text_from_html(html: str) -> str:
        """Extract readable text from HTML — naive but dependency-free."""
        # Remove scripts and styles
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
        # Remove tags
        text = re.sub(r"<[^>]+>", " ", html)
        # Decode common entities
        text = (
            text.replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
        )
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text
