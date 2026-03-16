# findata — 金融数据查询详细指南

## 功能

查询股票、板块、指数、债券等金融对象的结构化数据，输出 Excel 文件。

## 支持的查询对象
- 股票（A股、港股、美股）
- 板块、指数、股东
- 企业发行人、债券、非上市公司

## 支持的数据类型
- **实时行情**：现价、涨跌幅、盘口数据
- **量化数据**：技术指标、资金流向
- **报表数据**：营收、净利润、财务比率

## 配额限制
- 单次最多 **5 个实体**
- 单次最多 **3 个指标**
- 超限自动截断，说明文件中提示

## 查询示例

| 类型 | 示例 |
|---|---|
| 基础 | 东方财富的基本面 |
| 时间范围 | 贵州茅台最近一年的营业收入和净利润 |
| 实时行情 | 当前300059的实时买单 |
| 多实体对比 | 对比创业板指、沪深300、中证500春节以来的涨幅 |
| 超限示例 | "沪深前十大权重股的PE" → 仅返回前5名 |

## CLI

```bash
mx-skills findata "贵州茅台近期走势如何"
mx-skills findata "英伟达现在的最新价和涨跌幅" --output-dir ./data
```

## Python API

```python
import asyncio
from mx_skills import query_financial_data

result = asyncio.run(query_financial_data(query="贵州茅台近期走势如何"))
# result keys: file_path, description_path, row_count, query, error(optional)
```

## 输出
- `MX_FinData_<id>.xlsx` — 结构化数据（可能多个 sheet）
- `MX_FinData_<id>_description.txt` — 查询说明、字段含义、截断提示

## 注意
- 需要安装 Excel 依赖：`pip install "mx-skills[excel]"`
- 语句中必须包含明确的金融实体名称
- 面向结构化数据查询，不侧重主观分析
