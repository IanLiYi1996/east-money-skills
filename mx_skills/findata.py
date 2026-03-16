"""
Financial data query module.

Queries the East Money searchData API with a natural-language question,
parses the structured response, and writes results to Excel + description files.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any

from mx_skills._common import (
    API_BASE,
    async_post,
    build_tool_context,
    flatten_value,
    safe_filename,
)

logger = logging.getLogger("mx_skills.findata")

SEARCH_DATA_URL = f"{API_BASE}/proxy/b/mcp/tool/searchData"
DEFAULT_OUTPUT_DIR = Path("workspace") / "MX_FinData"

try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _ordered_keys(table: dict[str, Any], indicator_order: list[Any]) -> list[Any]:
    data_keys = [k for k in table.keys() if k != "headName"]
    key_map = {str(k): k for k in data_keys}
    preferred: list[Any] = []
    seen: set[str] = set()
    for key in indicator_order:
        key_str = str(key)
        if key_str in key_map and key_str not in seen:
            preferred.append(key_map[key_str])
            seen.add(key_str)
    for key in data_keys:
        key_str = str(key)
        if key_str not in seen:
            preferred.append(key)
            seen.add(key_str)
    return preferred


def _normalize_values(raw_values: list[Any], expected_len: int) -> list[str]:
    values = [flatten_value(v) for v in raw_values]
    if len(values) < expected_len:
        values.extend([""] * (expected_len - len(values)))
    return values[:expected_len]


def _return_code_map(block: dict[str, Any]) -> dict[str, str]:
    for key in ("returnCodeMap", "returnCodeNameMap", "codeMap"):
        data = block.get(key)
        if isinstance(data, dict):
            return {str(k): flatten_value(v) for k, v in data.items()}
    return {}


def _format_indicator_label(
    key: str, name_map: dict[str, Any], code_map: dict[str, str]
) -> str:
    mapped = name_map.get(key)
    if mapped is None and key.isdigit():
        mapped = name_map.get(int(key))
    if mapped not in (None, ""):
        return flatten_value(mapped)
    mapped_code = code_map.get(key)
    if mapped_code not in (None, ""):
        return flatten_value(mapped_code)
    if key.isdigit():
        return ""
    return key


def _table_to_rows_generic(
    table: Any, name_map: dict[str, str] | None
) -> list[dict[str, Any]]:
    name_map = name_map or {}
    if isinstance(table, list):
        if not table:
            return []
        if isinstance(table[0], dict):
            rows = table
        else:
            rows = [
                dict(zip([f"column_{i}" for i in range(len(table[0]))], row))
                for row in table
            ]
    elif isinstance(table, dict):
        vals = [v for v in table.values() if isinstance(v, list)]
        if vals and all(isinstance(v, list) for v in table.values()):
            n = len(vals[0])
            if all(len(v) == n for v in vals):
                cols = list(table.keys())
                rows = [
                    dict(zip(cols, [v[i] for v in table.values()])) for i in range(n)
                ]
            else:
                rows = []
        else:
            cols = table.get("columns") or table.get("fields") or []
            rows_data = table.get("rows") or table.get("data") or []
            if not cols and rows_data:
                cols = [f"column_{i}" for i in range(len(rows_data[0]))]
            rows = [dict(zip(cols, r)) for r in rows_data]
    else:
        return []

    return [{name_map.get(k, k): flatten_value(v) for k, v in row.items()} for row in rows]


def _table_to_rows(
    block: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    table = block.get("table") or {}
    name_map = block.get("nameMap") or {}
    if isinstance(name_map, list):
        name_map = {str(i): v for i, v in enumerate(name_map)}
    elif not isinstance(name_map, dict):
        name_map = {}

    if not isinstance(table, dict):
        rows = _table_to_rows_generic(table, name_map)
        fieldnames = list(rows[0].keys()) if rows else []
        return rows, fieldnames

    headers = table.get("headName") or []
    if not isinstance(headers, list):
        headers = []
    order = _ordered_keys(table, block.get("indicatorOrder") or [])
    entity_name = flatten_value(block.get("entityName") or "") or "指标"
    code_map = _return_code_map(block)

    rows: list[dict[str, Any]] = []
    data_key_count = len([key for key in table.keys() if key != "headName"])

    if len(headers) > 1 and data_key_count >= 1:
        fieldnames = [entity_name] + [flatten_value(h) for h in headers]
        for key in order:
            raw_values = table.get(key, [])
            if not isinstance(raw_values, list):
                raw_values = [raw_values]
            values = _normalize_values(raw_values, len(headers))
            label = _format_indicator_label(str(key), name_map, code_map)
            rows.append(dict(zip(fieldnames, [label] + values)))
        return rows, fieldnames

    if len(headers) == 1 and data_key_count >= 1:
        fieldnames = [entity_name, flatten_value(headers[0])]
        for key in order:
            raw_values = table.get(key, [])
            value = (
                raw_values[0]
                if isinstance(raw_values, list) and raw_values
                else raw_values
            )
            label = _format_indicator_label(str(key), name_map, code_map)
            rows.append(
                {fieldnames[0]: label, fieldnames[1]: flatten_value(value)}
            )
        return rows, fieldnames

    fallback_rows = _table_to_rows_generic(table, name_map)
    if fallback_rows:
        return fallback_rows, list(fallback_rows[0].keys())
    return [], []


def _safe_sheet_name(raw_name: Any, used_names: set[str]) -> str:
    name = flatten_value(raw_name).strip() or "表"
    name = re.sub(r"[:\\/?*\[\]]", "_", name)
    if len(name) > 31:
        name = name[:31]

    base = name or "表"
    candidate = base
    idx = 2
    while candidate in used_names:
        suffix = f"_{idx}"
        if len(base) + len(suffix) > 31:
            candidate = base[: 31 - len(suffix)] + suffix
        else:
            candidate = base + suffix
        idx += 1
    used_names.add(candidate)
    return candidate


def _extract_data_table_dto_list(
    api_result: Any,
) -> tuple[list[Any] | None, str | None]:
    """
    Extract dataTableDTOList from the API response.

    Supports both the new structure:
      data.searchDataResultDTO.dataTableDTOList
    and legacy structures:
      dataTableDTOList or data.dataTableDTOList
    """
    if not isinstance(api_result, dict):
        return None, "接口返回不是 JSON 对象"

    dto_list = api_result.get("dataTableDTOList")
    if isinstance(dto_list, list):
        return dto_list, None

    data_node = api_result.get("data")
    if isinstance(data_node, dict):
        search_result = data_node.get("searchDataResultDTO")
        if isinstance(search_result, dict):
            dto_list = search_result.get("dataTableDTOList")
            if isinstance(dto_list, list):
                return dto_list, None

        dto_list = data_node.get("dataTableDTOList")
        if isinstance(dto_list, list):
            return dto_list, None

    return None, "接口返回中无 data.searchDataResultDTO.dataTableDTOList"


def _check_business_status(api_result: Any) -> str | None:
    """
    Validate business status fields from the API response.

    Returns an error string if the response indicates failure, or None on success.
    """
    if not isinstance(api_result, dict):
        return "接口返回不是 JSON 对象"

    code = api_result.get("code")
    status = api_result.get("status")
    if code not in (None, 200) or status not in (None, 200):
        message = flatten_value(api_result.get("message") or "业务状态非成功")
        return f"接口业务错误: code={code}, status={status}, message={message}"
    return None


def _parse_data_table_response(
    api_result: Any,
) -> tuple[list[dict[str, Any]], list[str], int, str | None]:
    dto_list, extract_err = _extract_data_table_dto_list(api_result)
    if extract_err:
        return [], [], 0, extract_err
    if not dto_list:
        return [], [], 0, "接口返回的 dataTableDTOList 为空"

    condition_parts: list[str] = []
    tables: list[dict[str, Any]] = []
    total_rows = 0
    used_sheet_names: set[str] = set()

    for i, dto in enumerate(dto_list):
        if not isinstance(dto, dict):
            continue

        sheet_name = _safe_sheet_name(
            dto.get("title")
            or dto.get("inputTitle")
            or dto.get("entityName")
            or f"表{i + 1}",
            used_sheet_names,
        )
        condition = dto.get("condition")
        if condition is not None and condition != "":
            entity = dto.get("entityName") or sheet_name
            condition_parts.append(f"[{entity}]\n{condition}")

        rows, fieldnames = _table_to_rows(dto)
        if not rows:
            continue
        tables.append(
            {"sheet_name": sheet_name, "rows": rows, "fieldnames": fieldnames}
        )
        total_rows += len(rows)

    if not tables:
        return [], condition_parts, 0, "dataTableDTOList 中无有效 table 数据"
    return tables, condition_parts, total_rows, None


def _write_output_files(
    *,
    output_dir: Path,
    query_text: str,
    tables: list[dict[str, Any]],
    total_rows: int,
    condition_parts: list[str],
) -> tuple[Path, Path]:
    unique_suffix = uuid.uuid4().hex[:8]
    file_path = output_dir / f"MX_FinData_{unique_suffix}.xlsx"
    desc_path = output_dir / f"MX_FinData_{unique_suffix}_description.txt"

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        for table in tables:
            df = pd.DataFrame(table["rows"], columns=table["fieldnames"])
            df.to_excel(writer, sheet_name=table["sheet_name"], index=False)

    description_lines = [
        "金融数据查询结果说明",
        "=" * 40,
        f"查询内容: {query_text}",
        f"数据文件路径: {file_path}",
        f"描述文件路径: {desc_path}",
        f"数据行数: {total_rows}",
        f"表数量: {len(tables)}",
        f"Sheet 列表: {', '.join([t['sheet_name'] for t in tables])}",
    ]
    desc_path.write_text("\n".join(description_lines), encoding="utf-8")
    return file_path, desc_path


# ---------------------------------------------------------------------------
# Request builder
# ---------------------------------------------------------------------------


def _build_request_body(query: str) -> dict[str, Any]:
    return {
        "query": query,
        "toolContext": build_tool_context(),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def query_financial_data(
    query: str,
    output_dir: Path | None = None,
    api_url: str | None = None,
) -> dict[str, Any]:
    """
    Query the East Money financial data API and write results to Excel.

    Args:
        query: Natural-language question (entity + indicator).
        output_dir: Directory for output files. Defaults to ``workspace/MX_FinData``.
        api_url: Override the default search-data endpoint URL.

    Returns:
        Dict with keys: file_path, description_path, row_count, query, and
        optionally error / raw_preview.
    """
    if not HAS_PANDAS:
        return {
            "file_path": None,
            "description_path": None,
            "row_count": 0,
            "query": query,
            "error": "pandas is required but not installed. Run: pip install pandas openpyxl",
        }

    output_dir = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    url = api_url or SEARCH_DATA_URL
    result: dict[str, Any] = {
        "file_path": None,
        "description_path": None,
        "row_count": 0,
        "query": query,
    }

    try:
        body = _build_request_body(query)
        data = await async_post(url, body)
    except Exception as exc:
        result["error"] = f"请求失败: {exc!s}"
        return result

    status_err = _check_business_status(data)
    if status_err:
        result["error"] = status_err
        result["raw_preview"] = json.dumps(data, ensure_ascii=False)[:500]
        return result

    tables, condition_parts, total_rows, err = _parse_data_table_response(data)
    if err:
        result["error"] = err
        result["raw_preview"] = json.dumps(data, ensure_ascii=False)[:500]
        return result

    try:
        file_path, desc_path = _write_output_files(
            output_dir=output_dir,
            query_text=query,
            tables=tables,
            total_rows=total_rows,
            condition_parts=condition_parts,
        )
    except Exception as exc:
        result["error"] = f"写入结果文件失败: {exc!s}"
        return result

    result["file_path"] = str(file_path)
    result["description_path"] = str(desc_path)
    result["row_count"] = total_rows
    return result
