# MX Skills Package Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the MX_Skills collection into a pip-installable Python package (`mx-skills`) with unified CLI and OpenClaw-compatible SKILL.md definitions.

**Architecture:** Shared infrastructure in `_common.py` (API key, HTTP transport, utilities). Four business modules each owning their domain logic. Single CLI entry point `mx-skills` with subcommands. SKILL.md files in `skills/` directory reference the package.

**Tech Stack:** Python 3.10+, httpx (async HTTP), pandas/openpyxl (optional, for Excel), argparse (CLI), setuptools (packaging)

**Spec:** `docs/superpowers/specs/2026-03-16-mx-skills-design.md`

---

## File Structure

| Action | Path | Responsibility |
|---|---|---|
| Create | `pyproject.toml` | Package metadata, dependencies, CLI entry point |
| Create | `.gitignore` | Exclude build artifacts, workspace output, .env |
| Create | `LICENSE` | MIT license |
| Create | `mx_skills/__init__.py` | Version, public API exports |
| Create | `mx_skills/_common.py` | `get_api_key()`, `build_tool_context()`, `async_post()`, `safe_filename()`, `flatten_value()` |
| Create | `mx_skills/finsearch.py` | `query_financial_news()` — news search, content extraction |
| Create | `mx_skills/findata.py` | `query_financial_data()` — table parsing, Excel output |
| Create | `mx_skills/macrodata.py` | `query_macro_data()` — frequency grouping, CSV output |
| Create | `mx_skills/stockpick.py` | `query_stock_pick()` — column mapping, CSV output |
| Create | `mx_skills/cli.py` | `main()` — argparse with 4 subcommands |
| Create | `skills/MX_FinSearch/SKILL.md` | OpenClaw skill definition for finsearch |
| Create | `skills/MX_FinData/SKILL.md` | OpenClaw skill definition for findata |
| Create | `skills/MX_MacroData/SKILL.md` | OpenClaw skill definition for macrodata |
| Create | `skills/MX_StockPick/SKILL.md` | OpenClaw skill definition for stockpick |
| Create | `README.md` | Chinese documentation |
| Create | `README_EN.md` | English documentation (brief) |

---

## Chunk 1: Project Scaffolding

### Task 1: Create project configuration files

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `LICENSE`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "mx-skills"
version = "0.1.0"
description = "East Money MiaoXiang Financial Skills - Financial news, data query, macro data, stock screening"
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
authors = [{ name = "IanLiYi1996" }]

[project.urls]
Homepage = "https://github.com/IanLiYi1996/east-money-skills"

[project.scripts]
mx-skills = "mx_skills.cli:main"

dependencies = ["httpx>=0.24"]

[project.optional-dependencies]
excel = ["pandas>=1.5", "openpyxl>=3.0"]
all = ["pandas>=1.5", "openpyxl>=3.0"]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"
```

- [ ] **Step 2: Create .gitignore**

```
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
workspace/
.env
*.xlsx
*.csv
.DS_Store
```

- [ ] **Step 3: Create LICENSE**

Standard MIT license with copyright holder `IanLiYi1996`, year 2026.

- [ ] **Step 4: Create mx_skills/__init__.py**

```python
"""East Money MiaoXiang Financial Skills."""

__version__ = "0.1.0"

from mx_skills.finsearch import query_financial_news
from mx_skills.findata import query_financial_data
from mx_skills.macrodata import query_macro_data
from mx_skills.stockpick import query_stock_pick

__all__ = [
    "query_financial_news",
    "query_financial_data",
    "query_macro_data",
    "query_stock_pick",
    "__version__",
]
```

Note: The imports will fail until the modules are created. This is expected — we create the file now for structure, it becomes functional after Tasks 3-6.

- [ ] **Step 5: Create mx_skills/__main__.py**

```python
"""Allow `python -m mx_skills` as CLI entry point."""
from mx_skills.cli import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Verify directory structure**

Run: `find mx_skills -type f && cat pyproject.toml | head -5`
Expected: See `mx_skills/__init__.py`, `mx_skills/__main__.py` and first lines of pyproject.toml.

- [ ] **Step 7: Commit scaffolding**

```bash
git add pyproject.toml .gitignore LICENSE mx_skills/__init__.py mx_skills/__main__.py
git commit -m "chore: scaffold project with pyproject.toml, license, and package init"
```

---

## Chunk 2: Shared Infrastructure

### Task 2: Create _common.py

**Files:**
- Create: `mx_skills/_common.py`
- Reference: `MX_Skills/MX_FinSearch/scripts/get_data.py` (safe_filename, extract_error_message)
- Reference: `MX_Skills/MX_FinData/scripts/get_data.py` (flatten_value, build_request_body)
- Reference: `MX_Skills/MX_MacroData/scripts/get_data.py` (safe_filename, flatten_value)

- [ ] **Step 1: Create _common.py with all shared functions**

```python
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
            "Please configure it before running:\n"
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
```

- [ ] **Step 2: Verify module imports**

Run: `cd /home/ec2-user/research/east-money-skills && python3 -c "from mx_skills._common import get_api_key, build_tool_context, safe_filename, flatten_value; print('OK')"`
Expected: `OK` (async_post needs httpx installed, but the sync functions should import fine)

- [ ] **Step 3: Commit**

```bash
git add mx_skills/_common.py
git commit -m "feat: add shared infrastructure module (_common.py)"
```

---

## Chunk 3: FinSearch Module

### Task 3: Create finsearch.py

**Files:**
- Create: `mx_skills/finsearch.py`
- Reference: `MX_Skills/MX_FinSearch/scripts/get_data.py`

Key changes from original:
- Migrate from `urllib.request` to `_common.async_post()`
- Use `_common.get_api_key()` instead of hardcoded empty string
- Use `_common.safe_filename()` instead of local `_safe_filename()`
- Replace `print()` with `logging`

- [ ] **Step 1: Create finsearch.py**

```python
"""Financial news and research search via East Money MiaoXiang API."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from mx_skills._common import (
    API_BASE,
    async_post,
    build_tool_context,
    safe_filename,
)

logger = logging.getLogger("mx_skills.finsearch")

SEARCH_NEWS_URL = f"{API_BASE}/proxy/b/mcp/tool/searchNews"
DEFAULT_OUTPUT_DIR = Path("workspace") / "MX_FinSearch"


def _extract_content(raw: dict[str, Any]) -> str:
    """Extract readable text from news API response payload."""
    if not isinstance(raw, dict):
        return ""

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
    Query time-sensitive financial information.

    Args:
        query: Natural language query text.
        output_dir: Directory for output files. Defaults to workspace/MX_FinSearch.
        save_to_file: Whether to save results to a .txt file.

    Returns:
        dict with keys: query, content, output_path, raw, error (optional).
    """
    query = (query or "").strip()
    if not query:
        return {"query": "", "content": "", "output_path": None, "raw": None, "error": "query is empty"}

    out_dir = Path(output_dir or DEFAULT_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {"query": query, "content": "", "output_path": None, "raw": None}

    payload = {
        "query": query,
        "toolContext": build_tool_context(),
    }

    try:
        raw = await async_post(SEARCH_NEWS_URL, payload)
    except RuntimeError as exc:
        result["error"] = str(exc)
        return result

    result["raw"] = raw
    content = _extract_content(raw)
    result["content"] = content

    if save_to_file and content:
        output_path = out_dir / f"financial_search_{safe_filename(query)}.txt"
        output_path.write_text(content, encoding="utf-8")
        result["output_path"] = str(output_path)
        logger.info("Saved: %s", output_path)

    return result
```

- [ ] **Step 2: Verify import**

Run: `python3 -c "from mx_skills.finsearch import query_financial_news; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add mx_skills/finsearch.py
git commit -m "feat: add finsearch module (news/research search)"
```

---

## Chunk 4: FinData Module

### Task 4: Create findata.py

**Files:**
- Create: `mx_skills/findata.py`
- Reference: `MX_Skills/MX_FinData/scripts/get_data.py`

Key changes from original:
- Use `_common.async_post()` instead of inline httpx calls
- Use `_common.get_api_key()`, `_common.flatten_value()`, `_common.safe_filename()`
- Remove `query_financial_data_direct()` passthrough alias
- Replace `print()` with `logging`
- Graceful error if pandas/openpyxl not installed

- [ ] **Step 1: Create findata.py**

Port the following from the original `MX_FinData/scripts/get_data.py` (all internal functions preserved, ~220 lines):

**Internal helpers (copy and adapt):**
- `_ordered_keys(table, indicator_order)` — lines 88-103, no changes needed
- `_normalize_values(raw_values, expected_len)` — lines 106-110, replace `_flatten_value` → `flatten_value`
- `_return_code_map(block)` — lines 113-118, replace `_flatten_value` → `flatten_value`
- `_format_indicator_label(key, name_map, code_map)` — lines 121-132, replace `_flatten_value` → `flatten_value`
- `_table_to_rows_generic(table, name_map)` — lines 135-165, replace `_flatten_value` → `flatten_value`
- `_table_to_rows(block)` — lines 168-214, uses above helpers
- `_safe_sheet_name(raw_name, used_names)` — lines 230-247, replace `_flatten_value` → `flatten_value`
- `_extract_data_table_dto_list(api_result)` — lines 250-277, no changes needed
- `_check_business_status(api_result)` — lines 280-295, replace `_flatten_value` → `flatten_value`. Note: original checks `code not in (None, 200)` — preserve this behavior.
- `_parse_data_table_response(api_result)` — lines 298-333, uses above helpers
- `_write_output_files(output_dir, query_text, tables, total_rows, condition_parts)` — lines 336-364, uses pandas

**Key replacements across ALL functions:**
- `_flatten_value(v)` → `flatten_value(v)` (imported from `_common`)
- `EM_API_KEY` variable → `get_api_key()` call
- Inline httpx POST → `async_post(SEARCH_DATA_URL, body)`
- `_build_request_body(query)` → local function using `build_tool_context()`
- Remove `query_financial_data_direct()` alias (line 444-449)
- Replace all `print()` with `logger.debug()`/`logger.info()`

The main public function:

```python
async def query_financial_data(
    query: str,
    output_dir: Path | None = None,
    api_url: str | None = None,
) -> dict[str, Any]:
    """
    Query financial data by natural language.

    Returns:
        dict with keys: file_path, description_path, row_count, query, error (optional).
    """
```

Add pandas import guard at module level:

```python
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
```

In `query_financial_data()`, check before writing Excel:

```python
if not HAS_PANDAS:
    result["error"] = (
        "pandas is required for Excel output. "
        "Install with: pip install 'mx-skills[excel]'"
    )
    return result
```

- [ ] **Step 2: Verify import**

Run: `python3 -c "from mx_skills.findata import query_financial_data; print('OK')"`
Expected: `OK` (or pandas warning if not installed, but no crash)

- [ ] **Step 3: Commit**

```bash
git add mx_skills/findata.py
git commit -m "feat: add findata module (financial data query + Excel output)"
```

---

## Chunk 5: MacroData Module

### Task 5: Create macrodata.py

**Files:**
- Create: `mx_skills/macrodata.py`
- Reference: `MX_Skills/MX_MacroData/scripts/get_data.py`

Key changes from original:
- Use `_common.async_post()` instead of inline httpx
- Use `_common.get_api_key()`, `_common.flatten_value()`, `_common.safe_filename()`
- Fix `DEFAULT_PAHT` typo → use full URL constant directly
- Fix `api_base` parameter being silently ignored → `url = api_url or SEARCH_MACRO_URL`
- Remove debug JSON file writing (lines 298-300)
- Replace all `print()` with `logging`
- Preserve `utf-8-sig` encoding for CSV files (BOM for Excel compatibility on Windows)
- Default output dir: `workspace/MX_MacroData` (original library defaulted to `cwd()`, now unified)

**Note on userId change:** Original macrodata uses random `user_xxx` as userId. Unified `build_tool_context()` uses `EM_API_KEY`. If `searchMacroData` rejects this, revert to local toolContext construction with random userId.

- [ ] **Step 1: Create macrodata.py**

Port the following from `MX_MacroData/scripts/get_data.py`:
- `_extract_frequency(entity_name)` — lines 81-89, extract frequency from entityName
- `_parse_macro_table(data_item)` — lines 92-169, parse macro data table format
- `_write_csv_file(rows, frequency, query, output_dir)` — lines 196-250, write frequency-grouped CSV. Preserve `utf-8-sig` encoding.

Replace:
- `DEFAULT_PAHT` → not needed, use `SEARCH_MACRO_URL` constant
- All `print()` → `logger.debug()` / `logger.info()`
- Raw JSON dump (lines 298-300) → remove entirely
- `api_base` override → `url = api_url or SEARCH_MACRO_URL`
- `_flatten_value()` → `flatten_value` from `_common`
- `_safe_filename()` → `safe_filename` from `_common`

```python
SEARCH_MACRO_URL = f"{API_BASE}/proxy/b/mcp/tool/searchMacroData"
DEFAULT_OUTPUT_DIR = Path("workspace") / "MX_MacroData"
```

Main public function:

```python
async def query_macro_data(
    query: str,
    output_dir: Path | None = None,
    api_url: str | None = None,
) -> dict[str, Any]:
    """
    Query macro economic data by natural language.

    Returns:
        dict with keys: csv_paths, description_path, row_counts, query, error (optional).
    """
```

Use `api_url` parameter when provided: `url = api_url or SEARCH_MACRO_URL`

- [ ] **Step 2: Verify import**

Run: `python3 -c "from mx_skills.macrodata import query_macro_data; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add mx_skills/macrodata.py
git commit -m "feat: add macrodata module (macro economic data query + CSV output)"
```

---

## Chunk 6: StockPick Module

### Task 6: Create stockpick.py

**Files:**
- Create: `mx_skills/stockpick.py`
- Reference: `MX_Skills/MX_StockPick/scripts/get_data.py`

Key changes from original:
- Remove `mcp_single_call_v2()` — replaced by `_common.async_post()`
- Use `_common.get_api_key()`, `_common.safe_filename()`
- Replace `print()` with `logging`
- Rename function from `query_MX_StockPick` to `query_stock_pick`

- [ ] **Step 1: Create stockpick.py**

Port the following from `MX_StockPick/scripts/get_data.py`:
- `_build_column_map()` — columns to Chinese name mapping
- `_columns_order()` — preserve column order from API response
- `_parse_partial_results_table()` — fallback Markdown table parser
- `_datalist_to_rows()` — datalist to rows conversion with Chinese column names

Remove `mcp_single_call_v2()` and `get_metadata()`. Instead, construct the payload directly:

```python
SELECT_SECURITY_URL = f"{API_BASE}/proxy/b/mcp/tool/selectSecurity"
DEFAULT_OUTPUT_DIR = Path("workspace") / "MX_StockPick"

async def query_stock_pick(
    query: str,
    select_type: str,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Screen stocks/funds/sectors by natural language.

    Args:
        query: Natural language screening criteria.
        select_type: One of: A股, 港股, 美股, 基金, ETF, 可转债, 板块.
        output_dir: Directory for output files.

    Returns:
        dict with keys: csv_path, description_path, row_count, query, select_type, error (optional).
    """
    output_dir = Path(output_dir or DEFAULT_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "csv_path": None, "description_path": None,
        "row_count": 0, "query": query, "select_type": select_type,
    }

    payload = {
        "query": query,
        "selectType": select_type,
        "toolContext": build_tool_context(),
    }

    try:
        raw = await async_post(SELECT_SECURITY_URL, payload)
    except RuntimeError as exc:
        result["error"] = str(exc)
        return result

    # async_post returns full JSON; original mcp_single_call_v2 returned result.json()["data"]
    # So we must unwrap the "data" layer first
    data = raw.get("data", raw)

    # Now traverse the nested response structure (matches original lines 247-251)
    all_results = data.get("allResults", {})
    inner_result = all_results.get("result", {})
    data_list = inner_result.get("dataList", [])
    columns = inner_result.get("columns", [])

    if not isinstance(data_list, list):
        data_list = []
    if not isinstance(columns, list):
        columns = []

    rows: list[dict[str, str]] = []
    data_source = ""

    if data_list:
        column_map = _build_column_map(columns)
        column_order = _columns_order(columns)
        rows = _datalist_to_rows(data_list, column_map, column_order)
        data_source = "dataList"

    # Fallback to partialResults Markdown table (original lines 264-268)
    if not rows:
        partial_results = data.get("partialResults")
        if partial_results:
            rows = _parse_partial_results_table(partial_results)
            data_source = "partialResults"

    if not rows:
        result["error"] = "No valid dataList and partialResults cannot be parsed"
        result["raw_preview"] = json.dumps(raw, ensure_ascii=False)[:500]
        return result

    # Write CSV and description (using utf-8-sig for Excel compatibility)
    fieldnames = list(rows[0].keys())
    safe_name = safe_filename(select_type + "_" + query)
    csv_path = output_dir / f"MX_StockPick_{safe_name}.csv"
    desc_path = output_dir / f"MX_StockPick_{safe_name}_description.txt"

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    # ... description file writing (same pattern as original lines 286-296)

    result["csv_path"] = str(csv_path)
    result["description_path"] = str(desc_path)
    result["row_count"] = len(rows)
    return result
```

- [ ] **Step 2: Verify import**

Run: `python3 -c "from mx_skills.stockpick import query_stock_pick; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add mx_skills/stockpick.py
git commit -m "feat: add stockpick module (stock/fund/sector screening + CSV output)"
```

---

## Chunk 7: Unified CLI

### Task 7: Create cli.py

**Files:**
- Create: `mx_skills/cli.py`

- [ ] **Step 1: Create cli.py with argparse subcommands**

```python
"""Unified CLI entry point for mx-skills."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys


def _run_async(coro):
    """Run an async coroutine from sync CLI context."""
    return asyncio.run(coro)


def _cmd_finsearch(args):
    from mx_skills.finsearch import query_financial_news
    from pathlib import Path

    out_dir = Path(args.output_dir) if args.output_dir else None
    result = _run_async(query_financial_news(
        query=args.query,
        output_dir=out_dir,
        save_to_file=not args.no_save,
    ))
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(2)
    if result.get("output_path"):
        print(f"Saved: {result['output_path']}")
    print(result.get("content", ""))


def _cmd_findata(args):
    from mx_skills.findata import query_financial_data
    from pathlib import Path

    out_dir = Path(args.output_dir) if args.output_dir else None
    result = _run_async(query_financial_data(query=args.query, output_dir=out_dir))
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(2)
    print(f"File: {result['file_path']}")
    print(f"Description: {result['description_path']}")
    print(f"Rows: {result['row_count']}")


def _cmd_macro(args):
    from mx_skills.macrodata import query_macro_data
    from pathlib import Path

    out_dir = Path(args.output_dir) if args.output_dir else None
    result = _run_async(query_macro_data(query=args.query, output_dir=out_dir))
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(2)
    print(f"CSV: {result['csv_paths']}")
    print(f"Description: {result['description_path']}")
    print(f"Rows: {result['row_counts']}")


def _cmd_stockpick(args):
    from mx_skills.stockpick import query_stock_pick
    from pathlib import Path

    out_dir = Path(args.output_dir) if args.output_dir else None
    result = _run_async(query_stock_pick(
        query=args.query,
        select_type=args.type,
        output_dir=out_dir,
    ))
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(2)
    print(f"CSV: {result['csv_path']}")
    print(f"Description: {result['description_path']}")
    print(f"Rows: {result['row_count']}")


def main():
    parser = argparse.ArgumentParser(
        prog="mx-skills",
        description="East Money MiaoXiang Financial Skills CLI",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable debug logging",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # finsearch
    p_fin = subparsers.add_parser("finsearch", help="Search financial news and research")
    p_fin.add_argument("query", help="Natural language query")
    p_fin.add_argument("--output-dir", help="Output directory")
    p_fin.add_argument("--no-save", action="store_true", help="Don't save to file")
    p_fin.set_defaults(func=_cmd_finsearch)

    # findata
    p_data = subparsers.add_parser("findata", help="Query financial data")
    p_data.add_argument("query", help="Natural language query")
    p_data.add_argument("--output-dir", help="Output directory")
    p_data.set_defaults(func=_cmd_findata)

    # macro
    p_macro = subparsers.add_parser("macro", help="Query macro economic data")
    p_macro.add_argument("query", help="Natural language query")
    p_macro.add_argument("--output-dir", help="Output directory")
    p_macro.set_defaults(func=_cmd_macro)

    # stockpick
    p_stock = subparsers.add_parser("stockpick", help="Screen stocks/funds/sectors")
    p_stock.add_argument("query", help="Natural language screening criteria")
    p_stock.add_argument(
        "--type", required=True,
        choices=["A股", "港股", "美股", "基金", "ETF", "可转债", "板块"],
        help="Security type to screen",
    )
    p_stock.add_argument("--output-dir", help="Output directory")
    p_stock.set_defaults(func=_cmd_stockpick)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s %(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)

    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify CLI help works**

Run: `python3 -m mx_skills.cli --help`
Expected: Shows usage with finsearch, findata, macro, stockpick subcommands.

Run: `python3 -m mx_skills.cli finsearch --help`
Expected: Shows finsearch usage with query, --output-dir, --no-save.

Run: `python3 -m mx_skills.cli stockpick --help`
Expected: Shows stockpick usage with query, --type (required), --output-dir.

- [ ] **Step 3: Commit**

```bash
git add mx_skills/cli.py
git commit -m "feat: add unified CLI entry point (mx-skills command)"
```

---

## Chunk 8: SKILL.md Files and README

### Task 8: Create updated SKILL.md files

**Files:**
- Create: `skills/MX_FinSearch/SKILL.md`
- Create: `skills/MX_FinData/SKILL.md`
- Create: `skills/MX_MacroData/SKILL.md`
- Create: `skills/MX_StockPick/SKILL.md`

- [ ] **Step 1: Create all four SKILL.md files**

Each SKILL.md preserves the original content structure but updates:
1. Frontmatter `metadata.openclaw.requires.env` → `["EM_API_KEY"]`
2. Frontmatter `metadata.openclaw.install` → `[{id: "pip-install", kind: "python", package: ".", label: "Install mx-skills package"}]`
3. "Quick Start" section → two methods: `mx-skills` CLI and Python API import
4. Code examples → use new function names (`query_stock_pick` not `query_select_stock`, etc.)
5. Remove references to `scripts/get_data.py` direct execution

Keep the original Chinese content, query examples, constraints (especially MacroData's strict input constraints), output file descriptions, and FAQ sections intact.

- [ ] **Step 2: Commit SKILL.md files**

```bash
git add skills/
git commit -m "feat: add updated SKILL.md files for all four skills"
```

### Task 9: Create README files

**Files:**
- Create: `README.md`
- Create: `README_EN.md`

- [ ] **Step 1: Create README.md (Chinese)**

Structure per spec:
1. Project title + one-liner description
2. Four sub-skills table (name, function, output format)
3. Quick start: `pip install`, `export EM_API_KEY`, example command for each
4. CLI usage: all subcommands with parameter tables
5. Python API: code examples showing `from mx_skills import ...`
6. Skill integration: how to use in Claude Code / OpenClaw
7. Output files table
8. Environment variables
9. License

- [ ] **Step 2: Create README_EN.md (English brief)**

Shorter English version covering: overview, install, quick CLI examples, Python API snippet, license.

- [ ] **Step 3: Commit README files**

```bash
git add README.md README_EN.md
git commit -m "docs: add Chinese and English README"
```

---

## Chunk 9: Git Init and GitHub Push

### Task 10: Initialize git repo and push to GitHub

- [ ] **Step 1: Verify all files are in place**

Run: `find . -type f -not -path './.git/*' -not -path './MX_Skills/*' -not -path './docs/*' -not -name '.DS_Store' | sort`

Expected file list:
```
./.gitignore
./LICENSE
./README.md
./README_EN.md
./mx_skills/__init__.py
./mx_skills/_common.py
./mx_skills/cli.py
./mx_skills/findata.py
./mx_skills/finsearch.py
./mx_skills/macrodata.py
./mx_skills/stockpick.py
./pyproject.toml
./skills/MX_FinData/SKILL.md
./skills/MX_FinSearch/SKILL.md
./skills/MX_MacroData/SKILL.md
./skills/MX_StockPick/SKILL.md
```

- [ ] **Step 2: Verify package can be imported**

Run: `cd /home/ec2-user/research/east-money-skills && python3 -c "import mx_skills; print(mx_skills.__version__)"`
Expected: `0.1.0`

- [ ] **Step 3: Verify CLI works**

Run: `python3 -m mx_skills.cli --help`
Expected: Shows all subcommands.

- [ ] **Step 4: Initialize git and make initial commit (if not already done incrementally)**

If commits were made incrementally per task, this step is a verification:
Run: `git log --oneline`
Expected: See commits from each task.

If starting fresh (no incremental commits):
```bash
git init
git add .gitignore LICENSE pyproject.toml README.md README_EN.md mx_skills/ skills/
git commit -m "feat: initial release of mx-skills package (v0.1.0)"
```

- [ ] **Step 5: Create GitHub repository and push**

```bash
gh repo create IanLiYi1996/east-money-skills --public --description "East Money MiaoXiang Financial Skills" --source . --push
```

If `gh` is not available, create repo manually on GitHub and:
```bash
git remote add origin https://github.com/IanLiYi1996/east-money-skills.git
git branch -M main
git push -u origin main
```

- [ ] **Step 6: Verify on GitHub**

Run: `gh repo view IanLiYi1996/east-money-skills`
Expected: Shows repo with description and README.

---

## Execution Order Summary

| Task | Description | Dependencies |
|---|---|---|
| 1 | Project scaffolding (pyproject, gitignore, license, init) | None |
| 2 | _common.py (shared infrastructure) | Task 1 |
| 3 | finsearch.py | Task 2 |
| 4 | findata.py | Task 2 |
| 5 | macrodata.py | Task 2 |
| 6 | stockpick.py | Task 2 |
| 7 | cli.py | Tasks 3-6 |
| 8 | SKILL.md files | Tasks 3-6 |
| 9 | README files | Tasks 3-7 |
| 10 | Git init + GitHub push | All above |

Tasks 3, 4, 5, 6 are independent and can be parallelized.
Tasks 8 and 9 are independent and can be parallelized.
