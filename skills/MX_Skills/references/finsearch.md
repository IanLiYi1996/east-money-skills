# finsearch — 金融资讯搜索详细指南

## 功能

通过自然语言检索时效性金融信息：新闻、公告、研报、政策解读。
优先从返回的 `llmSearchResponse` 字段提取正文内容。

## 查询示例

| 类型 | 示例查询 |
|---|---|
| 个股资讯 | 格力电器最新研报与公告 |
| 板块/主题 | 商业航天板块近期新闻 |
| 宏观/风险 | 美联储加息对A股影响 |
| 综合解读 | 今日大盘异动原因、北向资金流向解读 |

## CLI

```bash
mx-skills finsearch "寒武纪 688256 最新研报与公告"
mx-skills finsearch "商业航天板块近期新闻" --no-save
mx-skills finsearch "A股 汇率风险" --output-dir ./my_output
```

## Python API

```python
import asyncio
from mx_skills import query_financial_news

result = asyncio.run(query_financial_news(
    query="新能源板块近期政策与龙头公司动态",
    save_to_file=True,
))
# result keys: query, content, output_path, raw, error(optional)
```

## 输入建议
- 查询应包含至少一个明确目标：公司名、板块名、事件、政策或时间
- 对语义不清的问句，先做澄清再执行
- 汇总时保持关键数值、专有名词和原始语义不被篡改

## 输出
- `financial_search_<查询摘要>.txt` — 资讯正文
- `content` 字段 — 提取后的文本（优先 `llmSearchResponse`）
- `raw` 字段 — 原始接口返回，便于调试
