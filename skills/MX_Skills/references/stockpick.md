# stockpick — 选股/选板块/选基金详细指南

## 功能

通过自然语言进行证券筛选，输出带中文列名的 CSV 文件。

## 支持的标的类型

| --type 值 | 说明 |
|---|---|
| A股 | A股选股 |
| 港股 | 港股选股 |
| 美股 | 美股选股 |
| 基金 | 基金筛选 |
| ETF | ETF筛选 |
| 可转债 | 可转债筛选 |
| 板块 | 板块筛选 |

## 筛选能力

### 基础筛选
- 按股价、市值、涨跌幅、市盈率等财务/行情指标
- 按技术信号（连续上涨、突破均线等）
- 按主营业务、主要产品
- 按行业/概念板块成分股
- 获取指数成分股
- 推荐类查询

### A股进阶查询
- 高管信息、股东信息、龙虎榜
- 分红、并购、增发、回购
- 主营区域、券商金股

## 查询示例

| 类型 | 查询 | --type |
|---|---|---|
| A股 | 股价大于1000元的股票 | A股 |
| A股 | 创业板市盈率最低的50只 | A股 |
| 港股 | 港股的科技龙头 | 港股 |
| 美股 | 纳斯达克市值前30 | 美股 |
| 板块 | 今天涨幅最大板块 | 板块 |
| 基金 | 白酒主题基金 | 基金 |
| ETF | 规模超2亿的电力ETF | ETF |
| 可转债 | 价格低于110元、溢价率超5个点 | 可转债 |

## CLI

```bash
mx-skills stockpick --type A股 "股价大于100元的股票；涨跌幅；所属板块"
mx-skills stockpick --type 基金 "新能源混合基金近一年收益排名"
mx-skills stockpick --type 板块 "今天涨幅最大板块"
```

## Python API

```python
import asyncio
from mx_skills import query_stock_pick

result = asyncio.run(query_stock_pick(
    query="A股半导体板块市值前20",
    select_type="A股",
))
# result keys: csv_path, description_path, row_count, query, select_type, error(optional)
```

## 输出
- `MX_StockPick_<类型>_<查询>.csv` — 全量数据，中文列名，UTF-8 BOM 编码
- `MX_StockPick_<查询>_description.txt` — 查询内容、行数、列名说明

## 注意
- `--type` / `select_type` 为**必填参数**
- 实际支持的筛选条件远多于上述示例
