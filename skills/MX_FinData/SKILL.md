---
name: MX_FinData
description: Query structured financial data for stocks, sectors, indices, bonds, and more via natural language. Supports real-time quotes, quantitative data, and financial reports. Outputs Excel (.xlsx) and description files. Requires EM_API_KEY.
metadata:
  openclaw:
    requires:
      env: ["EM_API_KEY"]
      bins: ["python3"]
    install:
      - id: pip-install
        kind: python
        package: ".[excel]"
        label: "Install mx-skills package with Excel support"
---

# Financial Data Query (MX_FinData)

Query structured financial data via **natural language**. Data powered by East Money MiaoXiang.

## Supported Scope

### Queryable Entities
- Stocks (A-shares, Hong Kong, US)
- Sectors, indices, shareholders
- Bond issuers, bonds, unlisted companies
- Stock/fund/bond markets

### Data Types
- **Real-time quotes** (price, change%, order book)
- **Quantitative data** (technical indicators, capital flow)
- **Financial reports** (revenue, net profit, financial ratios)

### Query Limits
- **Max 5 entities** per query
- **Max 3 indicators** per query
- Excess entities/indicators are truncated with a note in the description file

## Query Examples

| Type | Example |
|---|---|
| Basic | Fundamentals of East Money |
| Time Range | Kweichow Moutai revenue and net profit for the past year |
| Real-time | Current real-time buy orders for 300059 |
| Multi-entity | Compare ChiNext, CSI 300, CSI 500 gains since Chinese New Year |

## Quick Start

### CLI

```bash
export EM_API_KEY="your_key"
mx-skills findata "Kweichow Moutai recent performance"
```

### Python API

```python
import asyncio
from mx_skills import query_financial_data

result = asyncio.run(query_financial_data(query="Kweichow Moutai recent performance"))
if "error" in result:
    print(result["error"])
else:
    print(f"File: {result['file_path']}")
    print(f"Rows: {result['row_count']}")
```

## Output

| File | Description |
|---|---|
| `MX_FinData_<id>.xlsx` | Structured data with entity/indicator sheets |
| `MX_FinData_<id>_description.txt` | Query description, field meanings, truncation notes |

## Environment Variables

| Variable | Description |
|---|---|
| `EM_API_KEY` | API authentication key (required) |

## Notes
- Focuses on structured data queries, not subjective analysis or investment advice
- Queries must contain explicit financial entity names
