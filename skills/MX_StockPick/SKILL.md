---
name: MX_StockPick
description: Screen stocks, sectors, funds, ETFs, and convertible bonds via natural language. Supports A-shares, Hong Kong stocks, US stocks, funds, ETFs, convertible bonds, and sectors. Outputs CSV with Chinese column names and description files. Requires EM_API_KEY.
metadata:
  openclaw:
    requires:
      env: ["EM_API_KEY"]
      bins: ["python3"]
    install:
      - id: pip-install
        kind: python
        package: "."
        label: "Install mx-skills package"
---

# Stock / Sector / Fund Screening (MX_StockPick)

Screen securities via **natural language**. Supported types:
- **A-shares**, **Hong Kong stocks**, **US stocks**
- **Funds**, **ETFs**, **Convertible bonds**, **Sectors**

## Screening Capabilities

### Basic Screening
- Filter by price, market cap, change%, PE ratio, and other financial/market indicators
- Filter by technical signals (consecutive rises, moving average breakouts)
- Filter by main business, primary products
- Filter by industry/concept sectors
- Get index constituents
- Recommendations for stocks, funds, sectors

### A-share Advanced Queries
- Executive information, shareholder data
- Dragon Tiger List (top movers)
- Dividends, M&A, additional offerings, buybacks
- Operating regions
- Broker stock picks

## Query Examples

| Type | Query | --type |
|---|---|---|
| A-shares | Stocks priced above 1000 RMB | A-shares |
| HK Stocks | Hong Kong tech leaders | HK stocks |
| US Stocks | Nasdaq top 30 by market cap | US stocks |
| Sectors | Top gaining sectors today | Sectors |
| Funds | Baijiu-themed funds | Funds |
| ETFs | Power ETFs with AUM over 200M | ETFs |
| Convertible Bonds | Convertible bonds priced below 110 with >5% premium | Convertible bonds |

## Quick Start

### CLI

```bash
export EM_API_KEY="your_key"
mx-skills stockpick --type A-shares "Stocks priced above 100 RMB with change% and sector"
```

### Python API

```python
import asyncio
from mx_skills import query_stock_pick

result = asyncio.run(query_stock_pick(
    query="A-share semiconductor sector top 20 by market cap",
    select_type="A-shares",
))
if "error" in result:
    print(result["error"])
else:
    print(f"CSV: {result['csv_path']}")
    print(f"Rows: {result['row_count']}")
```

## Output

| File | Description |
|---|---|
| `MX_StockPick_<query>.csv` | Full data with Chinese column names, UTF-8 BOM encoded |
| `MX_StockPick_<query>_description.txt` | Query details, row count, column descriptions |

## Parameters

| Parameter | Description | Required |
|---|---|---|
| `query` | Natural language screening criteria | Yes |
| `--type` | Security type: A-shares, HK stocks, US stocks, Funds, ETFs, Convertible bonds, Sectors | Yes |
| `--output-dir` | Custom output directory | No |

## Environment Variables

| Variable | Description |
|---|---|
| `EM_API_KEY` | API authentication key (required) |
