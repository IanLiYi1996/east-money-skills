"""
Macro data query: request API for JSON, convert to CSV and generate description files.

Query macro-economic data via natural language; results are saved as CSV and description txt.
"""

from __future__ import annotations

import csv
import logging
import re
import time
from pathlib import Path
from typing import Any

from mx_skills._common import (
    API_BASE,
    async_post,
    build_tool_context,
    flatten_value,
    safe_filename,
)

logger = logging.getLogger("mx_skills.macrodata")

SEARCH_MACRO_URL = f"{API_BASE}/proxy/b/mcp/tool/searchMacroData"
DEFAULT_OUTPUT_DIR = Path("workspace") / "MX_MacroData"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_frequency(entity_name: str) -> str:
    """
    Extract frequency info from entityName.

    Example: "GDP（年）" -> "年", "宏观数据（周）" -> "周"
    """
    match = re.search(r'[（(]([^）)]+)[）)]', entity_name)
    if match:
        return match.group(1)
    return "unknown"


def _parse_macro_table(data_item: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    """
    Parse macro data table format.

    Expected structure::

        {
            "table": {
                "EMM00000015": ["140.2万亿", "134.8万亿", ...],
                "headName": ["数据来源", "2025", "2024", ...]
            },
            "nameMap": {
                "EMM00000015": "中国:GDP:现价(元)",
                "headNameSub": "数据来源"
            },
            "entityName": "GDP（年）"
        }

    Returns:
        (rows, frequency) – parsed data rows and frequency string.
    """
    rows: list[dict[str, Any]] = []

    table = data_item.get("table", {})
    name_map = data_item.get("nameMap", {})
    entity_name = data_item.get("entityName", "")
    description = data_item.get("description", "")

    frequency = _extract_frequency(entity_name)

    if not table or not isinstance(table, dict):
        return rows, frequency

    # Column headers
    headers = table.get("headName", [])
    if not headers:
        headers = table.get("date", [])
        if not headers:
            return rows, frequency

    # Metric keys (exclude metadata keys)
    exclude_keys = {"headName", "headNameSub", "date"}
    metric_keys = [k for k in table.keys() if k not in exclude_keys]

    if not metric_keys:
        return rows, frequency

    for metric_key in metric_keys:
        values = table.get(metric_key, [])
        if not values:
            continue

        metric_name = name_map.get(metric_key, metric_key)

        row: dict[str, Any] = {
            "entity_name": entity_name,
            "entity_description": description,
            "indicator_code": metric_key,
            "indicator_name": metric_name,
            "frequency": frequency,
        }

        for i, header in enumerate(headers):
            if i < len(values):
                value = values[i]
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value) if value else ""
                row[header] = value

        rows.append(row)

    return rows, frequency


def _write_csv_file(
    rows: list[dict[str, Any]],
    frequency: str,
    query: str,
    output_dir: Path,
) -> tuple[Path | None, int]:
    """
    Write rows for a given frequency to a CSV file.

    Returns:
        (csv_path, row_count)
    """
    if not rows:
        return None, 0

    # Collect all field names preserving insertion order
    fieldnames_set: dict[str, None] = {}
    for row in rows:
        for k in row:
            fieldnames_set[k] = None

    # Priority fields first
    priority_fields = ["entity_name", "indicator_name", "indicator_code", "frequency", "数据来源"]
    fieldnames: list[str] = []
    for field in priority_fields:
        if field in fieldnames_set:
            fieldnames.append(field)
            del fieldnames_set[field]

    # Separate date columns from others and sort
    date_fields: list[str] = []
    other_fields: list[str] = []
    for field in fieldnames_set.keys():
        if (field.isdigit() and len(field) == 4) or re.match(r'^\d{4}-\d{2}-\d{2}$', field):
            date_fields.append(field)
        else:
            other_fields.append(field)

    date_fields.sort(reverse=True)
    other_fields.sort()

    fieldnames.extend(other_fields)
    fieldnames.extend(date_fields)

    safe_query = safe_filename(query)
    safe_freq = safe_filename(frequency)
    csv_path = output_dir / f"macro_data_{safe_query}_{safe_freq}.csv"

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: flatten_value(v) for k, v in row.items()})

    return csv_path, len(rows)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def query_macro_data(
    query: str,
    output_dir: Path | None = None,
    api_url: str | None = None,
) -> dict[str, Any]:
    """
    Query macro-economic data via natural language, convert JSON to CSV and description txt.

    Args:
        query: Natural language query, e.g. "中国GDP".
        output_dir: Directory to save CSV and txt files; defaults to *DEFAULT_OUTPUT_DIR*.
        api_url: Override API endpoint; defaults to *SEARCH_MACRO_URL*.

    Returns:
        Dict with keys: csv_paths, description_path, row_counts, query, error (optional).
    """
    url = api_url or SEARCH_MACRO_URL

    output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "csv_paths": [],
        "description_path": None,
        "row_counts": {},
        "query": query,
    }

    # ---- Request ----------------------------------------------------------
    try:
        payload = {"query": query, "toolContext": build_tool_context()}
        logger.info("POST %s query=%r", url, query)
        resp = await async_post(url, payload)
        data = resp.get("data")
    except Exception as exc:
        result["error"] = f"请求失败: {exc}"
        return result

    # ---- Parse response ---------------------------------------------------
    frequency_groups: dict[str, list[dict[str, Any]]] = {}
    description_parts: list[str] = []

    if isinstance(data, dict):
        # Path 1: text result
        if "result" in data:
            description_parts.append(f"文本结果: {data['result']}")

        # Path 2: dataTables
        data_list = data.get("dataTables", [])
        if data_list and isinstance(data_list, list):
            for item_list in data_list:
                rows, frequency = _parse_macro_table(item_list)
                if rows:
                    frequency_groups.setdefault(frequency, []).extend(rows)

                    entity_name = item_list.get("entityName", "")
                    description = item_list.get("description", "")
                    title = item_list.get("title", "")

                    if entity_name:
                        description_parts.append(f"实体名称 [{frequency}]: {entity_name}")
                    if description:
                        description_parts.append(f"描述 [{frequency}]: {description}")
                    if title:
                        description_parts.append(f"标题 [{frequency}]: {title}")

                    field_set = item_list.get("fieldSet", [])
                    if field_set and isinstance(field_set, list) and len(field_set) > 0:
                        field = field_set[0]
                        data_source = field.get("dataSource", "")
                        unit_name = field.get("unitName", "")
                        if data_source:
                            description_parts.append(f"数据来源 [{frequency}]: {data_source}")
                        if unit_name:
                            description_parts.append(f"单位 [{frequency}]: {unit_name}")

        # Path 3: rawDataTables (fallback)
        if not frequency_groups:
            raw_data_list = data.get("rawDataTables", [])
            if raw_data_list and isinstance(raw_data_list, list):
                for item_list in raw_data_list:
                    if not isinstance(item_list, list):
                        continue
                    for data_item in item_list:
                        if not isinstance(data_item, dict):
                            continue
                        rows, frequency = _parse_macro_table(data_item)
                        if rows:
                            frequency_groups.setdefault(frequency, []).extend(rows)

    if not frequency_groups:
        result["error"] = "无法解析表格数据"
        return result

    # ---- Write CSVs per frequency group -----------------------------------
    csv_paths: list[str] = []
    row_counts: dict[str, int] = {}

    for frequency, rows in frequency_groups.items():
        logger.info("Processing frequency [%s]: %d rows", frequency, len(rows))
        csv_path, row_count = _write_csv_file(rows, frequency, query, output_dir)
        if csv_path:
            csv_paths.append(str(csv_path))
            row_counts[frequency] = row_count
            logger.info("  Saved %s", csv_path)

    # ---- Write description txt --------------------------------------------
    desc_path = output_dir / f"macro_data_{safe_filename(query)}_description.txt"

    description_lines = [
        "宏观数据查询结果说明",
        "=" * 40,
        f"查询内容: {query}",
        f"数据频率组数: {len(frequency_groups)}",
        "",
        "各频率数据统计:",
    ]

    for frequency, count in row_counts.items():
        description_lines.append(f"  - {frequency}: {count} 行")

    description_lines.extend(["", "生成的文件:"])
    for p in csv_paths:
        description_lines.append(f"  - {Path(p).name}")

    description_lines.extend(["", "详细说明:"])

    if description_parts:
        seen: set[str] = set()
        for part in description_parts:
            if part not in seen:
                seen.add(part)
                description_lines.append(part)
    else:
        description_lines.append("（无额外说明）")

    description_lines.extend([
        "",
        "数据源信息:",
        f"接口: {url}",
        f"查询时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
    ])

    desc_path.write_text("\n".join(description_lines), encoding="utf-8")
    logger.info("Description saved to %s", desc_path)

    result["csv_paths"] = csv_paths
    result["description_path"] = str(desc_path)
    result["row_counts"] = row_counts
    return result
