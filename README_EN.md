# MX Skills - East Money MiaoXiang Financial Skills

A collection of financial data skills powered by **East Money MiaoXiang AI API**. Available as both a CLI tool and a Python library.

## Features

| Skill | Function | Output |
|---|---|---|
| **MX_FinSearch** | Financial news/research search | `.txt` |
| **MX_FinData** | Financial data query (stocks, bonds, etc.) | `.xlsx` + `.txt` |
| **MX_MacroData** | Macro economic data query | `.csv` + `.txt` |
| **MX_StockPick** | Stock/fund/sector screening | `.csv` + `.txt` |

## Quick Start

### Install as Claude Code Skill (Recommended)

```bash
claude plugin marketplace add IanLiYi1996/east-money-skills
claude plugin install MX_Skills@east-money-skills
```

### Or install via pip

```bash
pip install git+https://github.com/IanLiYi1996/east-money-skills.git
```

### Configure

```bash
# Get your API key from https://ai.eastmoney.com/chat
export EM_API_KEY="your_em_api_key"

# Search financial news
mx-skills finsearch "Latest research reports on Cambricon 688256"

# Query financial data
mx-skills findata "Kweichow Moutai revenue and net profit"

# Query macro data
mx-skills macro "China GDP"

# Screen stocks
mx-skills stockpick --type A股 "Stocks priced above 100 RMB"
```

## Python API

```python
import asyncio
from mx_skills import query_financial_news, query_stock_pick

result = asyncio.run(query_financial_news("New energy sector policy updates"))
print(result["content"])

result = asyncio.run(query_stock_pick("Semiconductor top 20 by market cap", select_type="A股"))
print(result["csv_path"])
```

## Environment Variables

| Variable | Description |
|---|---|
| `EM_API_KEY` | East Money MiaoXiang API key (required) |

## License

[MIT](LICENSE)
