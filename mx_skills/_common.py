"""Shared infrastructure for MX Skills API calls."""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from typing import Any

import httpx

logger = logging.getLogger("mx_skills")

API_BASE = "https://ai-saas.eastmoney.com"
DEFAULT_TIMEOUT = 30


def get_api_key() -> str:
    """Read EM_API_KEY from environment. Raise RuntimeError if missing."""
    key = os.environ.get("EM_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "EM_API_KEY environment variable is not set.\n"
            "Get your API key from: https://ai.eastmoney.com/chat\n"
            "Then configure it:\n"
            "  export EM_API_KEY=\"your_em_api_key\""
        )
    return key


def build_tool_context() -> dict[str, Any]:
    """Build toolContext dict with callId and userInfo."""
    return {
        "callId": f"call_{uuid.uuid4().hex[:8]}",
        "userInfo": {
            "userId": get_api_key(),
        },
    }


def _extract_error_message(body: str) -> str:
    """Return sanitized error details from response body."""
    body = (body or "").strip()
    if not body:
        return ""
    try:
        data = json.loads(body)
    except Exception:
        return body[:200]
    if isinstance(data, dict):
        for key in ("msg", "message", "error"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return body[:200]


async def async_post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Send POST request to East Money API.

    Args:
        url: Full API endpoint URL.
        payload: Complete request body (caller constructs it).

    Returns:
        Parsed JSON response as dict.

    Raises:
        RuntimeError: On HTTP errors, JSON decode failure, or timeout.
    """
    api_key = get_api_key()
    logger.debug("POST %s payload=%s", url, json.dumps(payload, ensure_ascii=False)[:200])

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "em_api_key": api_key,
                },
            )
            resp.raise_for_status()
    except httpx.TimeoutException as exc:
        raise RuntimeError(f"API request timed out after {DEFAULT_TIMEOUT}s: {url}") from exc
    except httpx.HTTPStatusError as exc:
        body = exc.response.text if exc.response else ""
        message = _extract_error_message(body) or f"HTTP {exc.response.status_code}"
        raise RuntimeError(f"API HTTP error: {message}") from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(f"API request failed: {exc}") from exc

    try:
        data = resp.json()
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError("API returned invalid JSON response.") from exc

    return data if isinstance(data, dict) else {"data": data}


def safe_filename(text: str, max_len: int = 80) -> str:
    """Convert query text to a safe filename segment."""
    cleaned = re.sub(r'[<>:"/\\|?*]', "_", text).strip().replace(" ", "_")
    return (cleaned[:max_len] or "query").strip("._")


def flatten_value(v: Any) -> str:
    """Convert a value to string; nested structures become JSON."""
    if v is None:
        return ""
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)
