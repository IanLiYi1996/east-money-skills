"""
Stock / Sector / Fund picker via the MCP selectSecurity tool.

Supports A-shares, HK stocks, US stocks, sectors, funds, ETFs, and
convertible bonds.  Returns a CSV with Chinese column headers and a
companion description file.
"""

from __future__ import annotations

import csv
import json
import logging
import re
from pathlib import Path
from typing import Any

from mx_skills._common import API_BASE, async_post, build_tool_context, safe_filename

logger = logging.getLogger("mx_skills.stockpick")

SELECT_SECURITY_URL = f"{API_BASE}/proxy/b/mcp/tool/selectSecurity"
DEFAULT_OUTPUT_DIR = Path("workspace") / "MX_StockPick"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_column_map(columns: list[dict[str, Any]]) -> dict[str, str]:
    """
    Build an English-to-Chinese column name mapping from the columns
    metadata returned by the API.
    """
    name_map: dict[str, str] = {}
    for col in columns or []:
        if not isinstance(col, dict):
            continue
        en_key = col.get("field", "") or col.get("name", "") or col.get("key", "")
        cn_name = col.get("displayName", "") or col.get("title", "") or col.get("label", "")
        cn_name = cn_name + ' ' + col.get('dateMsg') if col.get('dateMsg') else cn_name
        if en_key is not None and cn_name is not None:
            name_map[str(en_key)] = str(cn_name)
    return name_map


def _columns_order(columns: list[dict[str, Any]]) -> list[str]:
    """Return the ordered list of English column keys from *columns*."""
    order: list[str] = []
    for col in columns or []:
        if not isinstance(col, dict):
            continue
        en_key = col.get("field") or col.get("name") or col.get("key")
        if en_key is not None:
            order.append(str(en_key))
    return order


def _parse_partial_results_table(partial_results: str) -> list[dict[str, str]]:
    """
    Parse a Markdown table string from *partialResults* into a list of
    row dicts.  Format example:

        |序号|代码|名称|...|
        |---|---|---|...|
        |1|000001|平安银行|...|
    """
    if not partial_results or not isinstance(partial_results, str):
        return []
    lines = [ln.strip() for ln in partial_results.strip().splitlines() if ln.strip()]
    if not lines:
        return []

    def split_cells(line: str) -> list[str]:
        return [c.strip() for c in line.split("|") if c.strip() != ""]

    header_cells = split_cells(lines[0])
    if not header_cells:
        return []

    data_start = 1
    if data_start < len(lines) and re.match(r"^[\s\|\-]+$", lines[data_start]):
        data_start = 2

    rows: list[dict[str, str]] = []
    for i in range(data_start, len(lines)):
        cells = split_cells(lines[i])
        if len(cells) != len(header_cells):
            if len(cells) < len(header_cells):
                cells.extend([""] * (len(header_cells) - len(cells)))
            else:
                cells = cells[: len(header_cells)]
        rows.append(dict(zip(header_cells, cells)))
    return rows


def _datalist_to_rows(
    datalist: list[dict[str, Any]],
    column_map: dict[str, str],
    column_order: list[str],
) -> list[dict[str, str]]:
    """
    Replace English keys in each *datalist* row with their Chinese
    equivalents according to *column_map*, preserving the order given by
    *column_order*.
    """
    if not datalist:
        return []

    first = datalist[0]
    extra_keys = [k for k in first if k not in column_order]
    header_order = column_order + extra_keys

    rows: list[dict[str, str]] = []
    for row in datalist:
        if not isinstance(row, dict):
            continue
        cn_row: dict[str, str] = {}
        for en_key in header_order:
            if en_key not in row:
                continue
            cn_name = column_map.get(en_key, en_key)
            val = row[en_key]
            if val is None:
                cn_row[cn_name] = ""
            elif isinstance(val, (dict, list)):
                cn_row[cn_name] = json.dumps(val, ensure_ascii=False)
            else:
                cn_row[cn_name] = str(val)
        rows.append(cn_row)

    return rows


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def query_stock_pick(
    query: str,
    select_type: str,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Query the MCP selectSecurity tool for stocks, sectors, or funds.

    Args:
        query: Natural-language query, e.g. "股价大于1000元的股票".
        select_type: Target type such as A股, 港股, 美股, 基金, ETF,
            可转债, or 板块.
        output_dir: Directory for CSV and description files.  Defaults to
            ``workspace/MX_StockPick``.

    Returns:
        Dict with keys *csv_path*, *description_path*, *row_count*,
        *query*, *select_type*, and optionally *error*.
    """
    output_dir = output_dir or DEFAULT_OUTPUT_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "csv_path": None,
        "description_path": None,
        "row_count": 0,
        "query": query,
        "select_type": select_type,
    }

    try:
        payload = {
            "query": query,
            "selectType": select_type,
            "toolContext": build_tool_context(),
        }
        raw = await async_post(SELECT_SECURITY_URL, payload)
        data = raw.get("data", raw)  # unwrap the "data" envelope
    except Exception as e:
        result["error"] = f"MCP 调用失败: {e!s}"
        return result

    if not data or not isinstance(data, dict):
        result["error"] = "MCP 返回为空或非 JSON 对象"
        result["raw_preview"] = str(data)[:500] if data else ""
        return result

    # Full datalist (preferred) or fallback to partialResults markdown table
    dataList = data.get("allResults", {}).get("result", {}).get("dataList", [])
    if not isinstance(dataList, list):
        dataList = []

    columns = data.get("allResults", {}).get("result", {}).get("columns", [])
    if not isinstance(columns, list):
        columns = []

    rows: list[dict[str, str]] = []
    data_source = ""

    if dataList:
        column_map = _build_column_map(columns)
        column_order = _columns_order(columns)
        rows = _datalist_to_rows(dataList, column_map, column_order)
        data_source = "dataList"

    if not rows:
        partial_results = data.get("partialResults")
        if partial_results:
            rows = _parse_partial_results_table(partial_results)
            data_source = "partialResults"

    if not rows:
        result["error"] = "返回中无有效 datalist 且 partialResults 无法解析或为空"
        result["raw_preview"] = json.dumps(data, ensure_ascii=False)[:500]
        return result

    # ---- Write CSV and description file ----
    fieldnames = list(rows[0].keys())
    safe_name = safe_filename(select_type + '_' + query)
    csv_path = output_dir / f"MX_StockPick_{safe_name}.csv"
    desc_path = output_dir / f"MX_StockPick_{safe_name}_description.txt"

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    description_lines = [
        "选股/选板块/选基金 结果说明",
        "=" * 40,
        f"查询内容: {query}",
        f"数据行数: {len(rows)}（来源: {data_source}）",
        f"列名（中文）: {', '.join(fieldnames)}",
        "",
        "说明: 数据来源于 MCP 股票基金筛选；"
        + ("列名已按 columns 映射为中文。" if data_source == "dataList" else "表格来自 partialResults。"),
    ]
    desc_path.write_text("\n".join(description_lines), encoding="utf-8")

    result["csv_path"] = str(csv_path)
    result["description_path"] = str(desc_path)
    result["row_count"] = len(rows)
    logger.info(
        "query_stock_pick finished: %d rows written to %s",
        len(rows),
        csv_path,
    )
    return result
