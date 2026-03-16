# MX Skills - East Money Financial Skills Package Design

**Date:** 2026-03-16
**Status:** Approved
**Repo:** `IanLiYi1996/east-money-skills`

## Overview

Restructure the MX_Skills collection (4 sub-skills based on East Money "MiaoXiang" API) into a dual-purpose package:
1. A standard pip-installable Python package with unified CLI
2. A set of OpenClaw/Superpowers-compatible SKILL.md definitions

## Sub-Skills

| Skill | Function | API Endpoint | Output |
|---|---|---|---|
| MX_FinSearch | Financial news/research search | `/proxy/b/mcp/tool/searchNews` | `.txt` |
| MX_FinData | Financial data query (stocks, bonds, etc.) | `/proxy/b/mcp/tool/searchData` | `.xlsx` + `.txt` |
| MX_MacroData | Macro economic data query | `/proxy/b/mcp/tool/searchMacroData` | `.csv` + `.txt` |
| MX_StockPick | Stock/fund/sector screening | `/proxy/b/mcp/tool/selectSecurity` | `.csv` + `.txt` |

## Architecture

### Directory Structure

```
east-money-skills/
├── README.md
├── README_EN.md
├── LICENSE                     # MIT
├── pyproject.toml
├── .gitignore
├── mx_skills/
│   ├── __init__.py             # Version + public API exports
│   ├── _common.py              # Shared infrastructure
│   ├── cli.py                  # Unified CLI entry point
│   ├── finsearch.py            # Financial news search
│   ├── findata.py              # Financial data query
│   ├── macrodata.py            # Macro data query
│   └── stockpick.py            # Stock/fund screening
├── skills/
│   ├── MX_FinSearch/SKILL.md
│   ├── MX_FinData/SKILL.md
│   ├── MX_MacroData/SKILL.md
│   └── MX_StockPick/SKILL.md
└── docs/
    └── superpowers/specs/
        └── 2026-03-16-mx-skills-design.md
```

### Module Design

#### `_common.py` — Shared Infrastructure

Extracted from duplicated logic across 4 scripts:

| Function/Constant | Purpose | Current Duplication |
|---|---|---|
| `get_api_key()` | Read `os.environ["EM_API_KEY"]`, raise clear error if missing | 4 scripts, inconsistent (env var vs hardcoded) |
| `build_tool_context()` | Generate `callId` + `userInfo` request context (see contract below) | 4 scripts, varying implementations |
| `async_post(url, payload)` | Unified httpx async POST (see contract below) | 4 scripts (finsearch uses urllib, to be migrated) |
| `safe_filename(text, max_len)` | Convert query text to safe filename | 3 scripts, identical implementations |
| `flatten_value(v)` | Convert nested values to string | 2 scripts, identical |
| `DEFAULT_TIMEOUT = 30` | Unified timeout | Currently 15s/30s inconsistency |

##### `async_post()` Contract

```python
async def async_post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Send POST request to East Money API.

    Args:
        url: Full API endpoint URL.
        payload: Complete request body (module constructs it, including toolContext).

    Returns:
        Parsed JSON response as dict.

    Raises:
        RuntimeError: On HTTP errors (includes status code + truncated body).
        RuntimeError: On JSON decode failure.
        RuntimeError: On timeout (wraps httpx.TimeoutException).
    """
```

- Each module constructs its own full request body, calling `build_tool_context()` for the shared `toolContext` portion
- `async_post()` only handles HTTP transport: sets `em_api_key` header, timeout, sends request, parses JSON
- Module-specific fields (e.g. `selectType` for stockpick) are part of the module's payload, not `async_post`'s concern

##### `build_tool_context()` Contract

```python
def build_tool_context() -> dict[str, Any]:
    """
    Returns:
        {"callId": "call_<uuid8>", "userInfo": {"userId": "<EM_API_KEY>"}}
    """
```

- `userId` is set to `EM_API_KEY` value (this is what `findata` and `stockpick` currently use, and is the most likely expected format)
- `finsearch` currently omits `userInfo` — unified to include it for consistency

##### Migration Note: finsearch urllib -> httpx

`finsearch.py` currently uses `urllib.request` (synchronous, wrapped in `asyncio.to_thread`). During refactoring, migrate to `_common.async_post()` using native `httpx.AsyncClient`.

#### Business Modules

Each module retains only its domain-specific logic:

- **`finsearch.py`**: `query_financial_news()` + response content extraction
- **`findata.py`**: `query_financial_data()` + table parsing + Excel output
- **`macrodata.py`**: `query_macro_data()` + frequency grouping + CSV output
- **`stockpick.py`**: `query_stock_pick()` + column mapping + CSV output

#### Public API (`__init__.py`)

```python
from mx_skills.finsearch import query_financial_news
from mx_skills.findata import query_financial_data
from mx_skills.macrodata import query_macro_data
from mx_skills.stockpick import query_stock_pick

__version__ = "0.1.0"
```

### CLI Design (`cli.py`)

Unified entry point registered as `mx-skills`:

```bash
mx-skills <subcommand> [options]
```

| Subcommand | Module | Example |
|---|---|---|
| `finsearch` | `finsearch.py` | `mx-skills finsearch "QUERY"` |
| `findata` | `findata.py` | `mx-skills findata "QUERY"` |
| `macro` | `macrodata.py` | `mx-skills macro "QUERY"` |
| `stockpick` | `stockpick.py` | `mx-skills stockpick --type A股 "QUERY"` |

Common options:
- `--output-dir <path>`: Override default output directory
- `--no-save`: (finsearch only) Print result without writing to file
- `--verbose`: Enable debug logging

All subcommands use positional `QUERY` argument. `stockpick` additionally requires `--type` with enum values: `A股, 港股, 美股, 基金, ETF, 可转债, 板块`.

### Dependencies

```toml
dependencies = ["httpx>=0.24"]

[project.optional-dependencies]
excel = ["pandas>=1.5", "openpyxl>=3.0"]
all = ["pandas>=1.5", "openpyxl>=3.0"]
```

- Base install: `finsearch`, `macrodata`, `stockpick` work (httpx + stdlib csv)
- `pip install ".[excel]"`: enables `findata` Excel output
- `findata` gives clear error if pandas/openpyxl missing at call time (module imports fine, error raised when `query_financial_data()` is called)

### SKILL.md Adaptation

Each SKILL.md updated to:
1. Reference `mx-skills` CLI and Python API in "Quick Start"
2. Unified `metadata.openclaw.requires.env: ["EM_API_KEY"]`
3. Install section points to pip package: `pip install .`

### API Key Handling

All scripts unified to read `os.environ["EM_API_KEY"]`:
- `get_api_key()` in `_common.py` reads env var
- Missing key raises `RuntimeError` with clear instructions
- No hardcoded keys anywhere in codebase

### StockPick Special Handling

Current `mcp_single_call_v2` in `stockpick` is a standalone HTTP wrapper. Refactored to use `_common.async_post()`, with `stockpick` module only responsible for request body construction (including `selectType` field) and response parsing.

### Logging Strategy

- Use `logging` module throughout, replacing all `print()` statements
- Default level: `WARNING`
- CLI `--verbose` flag sets level to `DEBUG`
- No debug files written by default (remove `macrodata`'s raw JSON dump)

### Cleanup Notes

- Fix `DEFAULT_PAHT` typo in macrodata (rename to `DEFAULT_PATH`)
- Fix `macrodata.query_macro_data()` to respect `api_base` parameter (currently silently ignored)
- Remove `findata.query_financial_data_direct()` passthrough alias (not needed in new API)
- SKILL.md code examples updated to use new function names (e.g. `query_stock_pick` not `query_select_stock`)

## Packaging

```toml
[project]
name = "mx-skills"
version = "0.1.0"
description = "East Money MiaoXiang Financial Skills"
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
authors = [{ name = "IanLiYi1996" }]

[project.urls]
Homepage = "https://github.com/IanLiYi1996/east-money-skills"

[project.scripts]
mx-skills = "mx_skills.cli:main"

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"
```

## Out of Scope

- No CI/CD pipeline (can be added later)
- No unit tests (requires API mocking, can be added later)
- No PyPI publishing (install via `pip install git+...`)
- Original `MX_Skills/` directory not preserved in new repo

## README Structure

1. Project overview (one-liner + 4 sub-skill list)
2. Quick start (install, configure EM_API_KEY, example commands)
3. CLI usage (4 subcommands with parameter tables)
4. Python API (code examples)
5. Skill integration (Claude Code / OpenClaw usage)
6. Output file descriptions
7. Environment variables
8. License (MIT)
