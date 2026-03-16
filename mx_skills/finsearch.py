"""
Financial news search skill.

Queries the East Money MCP searchNews endpoint and optionally saves
the extracted content to a local file.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from mx_skills._common import API_BASE, async_post, build_tool_context, safe_filename

logger = logging.getLogger("mx_skills.finsearch")

SEARCH_NEWS_URL = f"{API_BASE}/proxy/b/mcp/tool/searchNews"
DEFAULT_OUTPUT_DIR = Path("workspace") / "MX_FinSearch"


def _extract_content(raw: dict[str, Any]) -> str:
    """Extract readable text from news API response payload."""
    if not isinstance(raw, dict):
        return ""

    # Common envelope format: {"data": {...}} / {"result": {...}}
    for wrapper_key in ("data", "result"):
        wrapped = raw.get(wrapper_key)
        if isinstance(wrapped, dict):
            nested = _extract_content(wrapped)
            if nested:
                return nested

    for key in ("llmSearchResponse", "searchResponse", "content", "answer", "summary"):
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False, indent=2)

    return json.dumps(raw, ensure_ascii=False, indent=2)


async def query_financial_news(
    query: str,
    output_dir: Path | None = None,
    save_to_file: bool = True,
) -> dict[str, Any]:
    """
    Query time-sensitive financial information from MCP news search.

    Returns:
        dict with keys: query, content, output_path, raw, error (optional)
    """
    query = (query or "").strip()
    if not query:
        return {
            "query": "",
            "content": "",
            "output_path": None,
            "raw": None,
            "error": "query is empty",
        }

    out_dir = Path(output_dir or DEFAULT_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {"query": query, "content": "", "output_path": None, "raw": None}
    try:
        payload = {"query": query, "toolContext": build_tool_context()}
        raw = await async_post(SEARCH_NEWS_URL, payload)
    except Exception as exc:
        logger.error("News API request failed: %s", exc)
        result["error"] = str(exc)
        return result

    result["raw"] = raw
    content = _extract_content(raw)
    result["content"] = content

    if save_to_file and content:
        output_path = out_dir / f"financial_search_{safe_filename(query)}.txt"
        output_path.write_text(content, encoding="utf-8")
        result["output_path"] = str(output_path)
        logger.info("Saved search results to %s", output_path)

    return result
