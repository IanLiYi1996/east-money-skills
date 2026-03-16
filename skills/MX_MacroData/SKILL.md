---
name: MX_MacroData
description: Query macro economic data via natural language. Returns CSV files grouped by frequency (annual, quarterly, monthly, etc.) with description files. Strict input constraints require explicit entities, time ranges, and indicators. Requires EM_API_KEY.
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

# Macro Economic Data Query (MX_MacroData)

Query macro economic data via **natural language**. Results are converted to **CSV** files grouped by frequency, with a **description** file.

## CRITICAL Input Constraints

**This tool is a strict data executor. All inputs must be absolutely explicit.**

### 1. No Ambiguous Regions
- BAD: "GDP of East China cities"
- GOOD: "GDP of Shanghai, Nanjing, Hangzhou, Hefei, Fuzhou"

### 2. No Ambiguous Commodities
- BAD: "Rare earth metal prices"
- GOOD: "Prices of praseodymium-neodymium oxide, dysprosium oxide, terbium oxide"

### 3. No Relative Rankings
- BAD: "GDP Top 5 countries' gold reserves"
- GOOD: "Gold reserves of USA, China, Germany, Japan, India"

### 4. No Relative Time
- BAD: "Stock market during the 2008 crisis"
- GOOD: "S&P 500 performance from 2007-10-01 to 2009-03-31"

### 5. No Macro Generalizations
- BAD: "Chinese economy data"
- GOOD: "China GDP YoY growth, China CPI YoY"

## Supported Data

- **Economic Indicators**: GDP, CPI, PPI, PMI, unemployment rate, industrial value added
- **Monetary/Financial**: M1/M2 money supply, social financing, bond yields, exchange rates
- **Commodity Prices**: Gold, silver, crude oil, copper, specific rare earth oxides
- **Multi-frequency**: Automatic grouping by year/quarter/month/week/day

## Query Examples

| Type | Correct Query |
|---|---|
| Domestic Economy | GDP data for Shanghai, Jiangsu, Zhejiang, Anhui, Fujian |
| Money Supply | M2 money supply for China, India, Brazil |
| Commodity Prices | Spot prices of praseodymium-neodymium oxide, copper, aluminum |
| Historical Events | S&P 500 from 2007-10-01 to 2009-03-31 |

## Quick Start

### CLI

```bash
export EM_API_KEY="your_key"
mx-skills macro "China GDP"
```

### Python API

```python
import asyncio
from mx_skills import query_macro_data

result = asyncio.run(query_macro_data(query="China GDP"))
if "error" in result:
    print(result["error"])
else:
    print(f"CSV files: {result['csv_paths']}")
    print(f"Row counts: {result['row_counts']}")
```

## Output

| File | Description |
|---|---|
| `macro_data_<query>_<frequency>.csv` | Data grouped by frequency, UTF-8 BOM encoded |
| `macro_data_<query>_description.txt` | Statistics, data sources, and units |

## Environment Variables

| Variable | Description |
|---|---|
| `EM_API_KEY` | API authentication key (required) |
