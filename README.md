# MX Skills - East Money MiaoXiang Financial Skills

基于东方财富**妙想大模型** API 的金融数据技能集，支持 CLI 命令行和 Python API 两种使用方式。

## 功能概览

| 技能 | 功能 | 输出格式 |
|---|---|---|
| **MX_FinSearch** | 金融资讯搜索（新闻、公告、研报） | `.txt` |
| **MX_FinData** | 金融数据查询（股票、债券、基金等结构化数据） | `.xlsx` + `.txt` |
| **MX_MacroData** | 宏观经济数据查询（GDP、CPI、货币供应等） | `.csv` + `.txt` |
| **MX_StockPick** | 选股 / 选板块 / 选基金 | `.csv` + `.txt` |

## 快速开始

### 1. 安装

#### 方式一：Claude Code Skill（推荐）

```bash
# 注册 marketplace（只需一次）
claude plugin marketplace add IanLiYi1996/east-money-skills

# 安装 skill
claude plugin install MX_Skills@east-money-skills
```

安装后在 Claude Code 中提到股票、选股、研报、宏观数据等金融话题时，技能会自动触发。

#### 方式二：pip 安装（独立使用）

```bash
# 基础安装（finsearch、macrodata、stockpick 可用）
pip install git+https://github.com/IanLiYi1996/east-money-skills.git

# 完整安装（包含 findata 的 Excel 输出支持）
pip install "mx-skills[all] @ git+https://github.com/IanLiYi1996/east-money-skills.git"
```

### 2. 配置 API Key

```bash
export EM_API_KEY="your_em_api_key"
```

> 请从 [https://ai.eastmoney.com/chat](https://ai.eastmoney.com/chat) 获取 API Key

### 3. 使用示例

```bash
# 搜索金融资讯
mx-skills finsearch "寒武纪 688256 最新研报与公告"

# 查询金融数据
mx-skills findata "贵州茅台最近一年的营业收入和净利润"

# 查询宏观数据
mx-skills macro "中国GDP"

# 选股
mx-skills stockpick --type A股 "股价大于100元的股票"
```

## CLI 使用说明

```bash
mx-skills <subcommand> [options]
```

### finsearch — 金融资讯搜索

```bash
mx-skills finsearch "查询内容" [--no-save] [--output-dir DIR]
```

| 参数 | 说明 | 必填 |
|---|---|---|
| `query` | 自然语言查询 | 是 |
| `--no-save` | 仅输出，不保存文件 | 否 |
| `--output-dir` | 输出目录 | 否 |

### findata — 金融数据查询

```bash
mx-skills findata "查询内容" [--output-dir DIR]
```

| 参数 | 说明 | 必填 |
|---|---|---|
| `query` | 自然语言查询（含实体+指标） | 是 |
| `--output-dir` | 输出目录 | 否 |

> 注意：单次查询最多 5 个实体、3 个指标

### macro — 宏观数据查询

```bash
mx-skills macro "查询内容" [--output-dir DIR]
```

| 参数 | 说明 | 必填 |
|---|---|---|
| `query` | 自然语言查询（需明确指标和地域） | 是 |
| `--output-dir` | 输出目录 | 否 |

> 注意：查询必须包含明确的实体、时间和指标，禁止模糊表述

### stockpick — 选股 / 选板块 / 选基金

```bash
mx-skills stockpick --type <类型> "查询内容" [--output-dir DIR]
```

| 参数 | 说明 | 必填 |
|---|---|---|
| `query` | 自然语言筛选条件 | 是 |
| `--type` | 标的类型：`A股` `港股` `美股` `基金` `ETF` `可转债` `板块` | 是 |
| `--output-dir` | 输出目录 | 否 |

### 通用选项

| 选项 | 说明 |
|---|---|
| `--verbose` / `-v` | 开启调试日志 |

## Python API

```python
import asyncio
from mx_skills import (
    query_financial_news,
    query_financial_data,
    query_macro_data,
    query_stock_pick,
)

# 金融资讯搜索
result = asyncio.run(query_financial_news("新能源板块近期政策"))
print(result["content"])

# 金融数据查询
result = asyncio.run(query_financial_data("东方财富基本面"))
print(result["file_path"])

# 宏观数据查询
result = asyncio.run(query_macro_data("中国近五年GDP"))
print(result["csv_paths"])

# 选股
result = asyncio.run(query_stock_pick("半导体板块市值前20", select_type="A股"))
print(result["csv_path"])
```

## Skill 集成

本项目同时提供 OpenClaw/Claude Code 兼容的 Skill 定义，位于 `skills/` 目录：

```
skills/MX_Skills/
├── SKILL.md                      # 主技能定义
└── references/
    ├── finsearch.md              # 金融资讯搜索详细指南
    ├── findata.md                # 金融数据查询详细指南
    ├── macro.md                  # 宏观数据查询详细指南
    └── stockpick.md              # 选股选基金详细指南
```

## 输出文件说明

| 模块 | 文件格式 | 说明 |
|---|---|---|
| finsearch | `financial_search_*.txt` | 资讯正文 |
| findata | `MX_FinData_*.xlsx` + `*_description.txt` | 结构化数据表 + 说明 |
| macrodata | `macro_data_*_<频率>.csv` + `*_description.txt` | 按频率分组的 CSV + 说明 |
| stockpick | `MX_StockPick_*.csv` + `*_description.txt` | 中文列名 CSV + 说明 |

## 环境变量

| 变量 | 说明 | 必填 |
|---|---|---|
| `EM_API_KEY` | 东方财富妙想 API 鉴权密钥 | 是 |

## License

[MIT](LICENSE)
