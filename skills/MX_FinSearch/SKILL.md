---
name: MX_FinSearch
description: Search real-time financial news, announcements, and research reports via natural language. Returns readable content and optionally saves to local text files. Requires EM_API_KEY.
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

# Financial News Search (MX_FinSearch)

Search real-time financial information via **natural language queries**. Use cases include:
- Latest news and policy updates
- Company announcements and event tracking
- Broker research reports and market analysis
- Impact analysis of macro events on markets/sectors

## Supported Query Types

| Type | Example Query |
|---|---|
| Stock News | Latest research reports on Gree Electric |
| Sector/Theme | Recent news on commercial aerospace sector |
| Macro/Risk | Impact of Fed rate hike on A-shares |
| Market Overview | Reasons for today's market volatility |

## Quick Start

### CLI

```bash
export EM_API_KEY="your_key"
mx-skills finsearch "Latest research reports and announcements for Cambricon 688256"
```

### Python API

```python
import asyncio
from mx_skills import query_financial_news

result = asyncio.run(query_financial_news(
    query="New energy sector policy updates and leading companies",
    save_to_file=True,
))
if "error" in result:
    print(result["error"])
else:
    print(result["content"])
    if result.get("output_path"):
        print("Saved to:", result["output_path"])
```

## Output

| File | Description |
|---|---|
| `financial_search_<query_summary>.txt` | Extracted news content (prefers `llmSearchResponse`) |

## Parameters

| Parameter | Description | Required |
|---|---|---|
| `query` | Natural language query text | Yes |
| `--no-save` | Print result only, don't save to file | No |
| `--output-dir` | Custom output directory | No |

## Environment Variables

| Variable | Description |
|---|---|
| `EM_API_KEY` | API authentication key (required) |

## Input Guidelines
- Queries should contain at least one clear target: company, sector, event, policy, or time range
- For ambiguous queries, clarify before executing
- Summaries preserve key numbers, proper nouns, and original semantics
