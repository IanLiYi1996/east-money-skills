---
name: MX_Skills
description: 东方财富妙想金融数据技能集。查询中国A股/港股/美股行情、金融资讯新闻研报、宏观经济数据(GDP/CPI/PMI)、选股选基金选板块。当用户提到股票查询、金融数据、股价、研报、公告、选股、板块筛选、宏观数据、市盈率、营收、涨跌幅、ETF、可转债、基金筛选、东方财富、妙想、A股分析、北向资金、龙虎榜等金融相关话题时使用此技能。Use this skill for any Chinese financial market data query, stock screening, financial news search, or macro economic data retrieval via East Money MiaoXiang API. Requires EM_API_KEY.
metadata:
  openclaw:
    requires:
      env: ["EM_API_KEY"]
      bins: ["python3"]
    install:
      - id: pip-install
        kind: python
        package: ".[all]"
        label: "Install mx-skills package"
---

# MX Skills — 东方财富妙想金融数据技能集

基于东方财富**妙想大模型 API** 的一站式金融数据工具，支持 CLI 和 Python API 两种调用方式。

## 四大功能模块

| 模块 | 功能 | 适用场景 | 输出 |
|---|---|---|---|
| **finsearch** | 金融资讯搜索 | 新闻、公告、研报、政策动态 | `.txt` |
| **findata** | 金融数据查询 | 股价、财报、估值、资金流向 | `.xlsx` + `.txt` |
| **macro** | 宏观经济数据 | GDP、CPI、PMI、货币供应、商品价格 | `.csv` + `.txt` |
| **stockpick** | 选股/选板块/选基金 | A股/港股/美股筛选、ETF、可转债 | `.csv` + `.txt` |

## 如何选择模块

- 用户想**了解最新消息、研报、公告** → `finsearch`
- 用户想**查具体指标数据**（股价、营收、PE 等） → `findata`
- 用户想查**宏观经济指标**（GDP、CPI、利率等） → `macro`
- 用户想**筛选/推荐股票、基金、板块** → `stockpick`

> 各模块详细用法见 `references/` 目录下对应文档。遇到复杂需求时，可组合多个模块。

## 前提条件

```bash
# 安装
pip install git+https://github.com/IanLiYi1996/east-money-skills.git

# 配置 API Key（必填，从东方财富官网获取）
export EM_API_KEY="your_em_api_key"
```

## 快速示例

### CLI 调用

```bash
# 搜索金融资讯
mx-skills finsearch "寒武纪 688256 最新研报与公告"

# 查询金融数据（输出 Excel）
mx-skills findata "贵州茅台最近一年的营业收入和净利润"

# 查询宏观数据（输出 CSV）
mx-skills macro "中国2020年至2025年GDP"

# 选股（必须指定 --type）
mx-skills stockpick --type A股 "股价大于100元的半导体股票"
```

### Python API 调用

```python
import asyncio
from mx_skills import (
    query_financial_news,
    query_financial_data,
    query_macro_data,
    query_stock_pick,
)

# 金融资讯
result = asyncio.run(query_financial_news("新能源板块近期政策"))
print(result["content"])

# 金融数据
result = asyncio.run(query_financial_data("东方财富基本面"))
print(f"Excel: {result['file_path']}, 行数: {result['row_count']}")

# 宏观数据
result = asyncio.run(query_macro_data("中国近五年GDP"))
print(f"CSV: {result['csv_paths']}")

# 选股
result = asyncio.run(query_stock_pick("半导体板块市值前20", select_type="A股"))
print(f"CSV: {result['csv_path']}, 行数: {result['row_count']}")
```

## 各模块查询限制

### findata 限制
- 单次最多 **5 个实体**、**3 个指标**
- 超限部分自动截断并在说明文件中提示

### macro 严格输入约束
宏观数据模块要求**所有输入必须绝对明确**，禁止模糊表述：
- 禁止模糊地域（如"华东五市"）→ 必须列出具体省市名
- 禁止模糊商品（如"稀土金属"）→ 必须列出具体品种名
- 禁止相对时间（如"过去三年"）→ 必须转换为 `YYYY-MM-DD`
- 禁止宏观泛指（如"中国经济"）→ 必须指定具体指标名

> 调用 macro 前，应先将用户的模糊需求解包为明确查询。详见 `references/macro.md`。

### stockpick 必填参数
- `--type` / `select_type` 为必填，可选值：`A股`、`港股`、`美股`、`基金`、`ETF`、`可转债`、`板块`

## 输出文件

| 模块 | 文件 | 说明 |
|---|---|---|
| finsearch | `financial_search_*.txt` | 资讯正文 |
| findata | `MX_FinData_*.xlsx` + `*_description.txt` | 结构化数据表 + 说明 |
| macro | `macro_data_*_<频率>.csv` + `*_description.txt` | 按频率分组的 CSV + 说明 |
| stockpick | `MX_StockPick_*.csv` + `*_description.txt` | 中文列名 CSV + 说明 |

所有输出默认保存在 `workspace/` 子目录中，可通过 `--output-dir` 覆盖。

## 通用选项

| 选项 | 说明 |
|---|---|
| `--verbose` / `-v` | 开启调试日志 |
| `--output-dir DIR` | 自定义输出目录 |
| `--no-save` | 仅 finsearch 可用，只输出不保存文件 |

## 环境变量

| 变量 | 说明 |
|---|---|
| `EM_API_KEY` | 东方财富妙想 API 鉴权密钥（必填） |

## 合规说明
- 禁止在代码或提示词中硬编码 API Key
- 检索失败时不得编造数据，应返回明确错误
- 本技能面向结构化数据查询，不提供投资建议
