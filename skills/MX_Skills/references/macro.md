# macro — 宏观经济数据查询详细指南

## 功能

查询宏观经济数据，按频率（年/季/月/周/日）分组输出 CSV 文件。

## 支持的数据范围
- **经济指标**：GDP、CPI、PPI、PMI、失业率、工业增加值
- **货币金融**：M1/M2 货币供应量、社融规模、国债利率、汇率
- **商品价格**：黄金、白银、原油、铜、特定稀土氧化物

## 严格输入约束

本模块为严格的数据执行器，**所有输入必须绝对明确**。调用前必须完成"语义解包"。

### 禁止的输入 → 正确的输入

| 规则 | 禁止 | 正确 |
|---|---|---|
| 模糊地域 | "华东五市GDP" | "上海市、南京市、杭州市、合肥市、福州市的GDP" |
| 模糊商品 | "稀土价格走势" | "氧化镨钕、氧化镝、氧化铽的价格走势" |
| 相对排名 | "GDP Top 5国家的黄金储备" | "美国、中国、德国、日本、印度的黄金储备" |
| 相对时间 | "过去三年的CPI" | "中国2023-01至2026-01的CPI同比" |
| 宏观泛指 | "中国经济数据" | "中国GDP同比增速、中国CPI同比" |

### 调用前的语义解包流程

1. 识别用户查询中的模糊表述
2. 将地域集合展开为具体省市/国家名
3. 将商品类别展开为具体品种
4. 将相对时间转换为 `YYYY-MM-DD` 或 `YYYY-Qx`
5. 将宏观概念细化为具体指标名
6. 用解包后的明确查询调用本模块

## CLI

```bash
mx-skills macro "中国GDP"
mx-skills macro "美国、中国、德国的非农就业数据"
mx-skills macro "标普500指数在2007-10-01至2009-03-31期间的走势"
```

## Python API

```python
import asyncio
from mx_skills import query_macro_data

result = asyncio.run(query_macro_data(query="中国近五年GDP"))
# result keys: csv_paths, description_path, row_counts, query, error(optional)
```

## 输出
- `macro_data_<查询>_<频率>.csv` — 按频率分组，UTF-8 BOM 编码
- `macro_data_<查询>_description.txt` — 数据统计、来源、单位
