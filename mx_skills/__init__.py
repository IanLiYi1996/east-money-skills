"""East Money MiaoXiang Financial Skills."""

__version__ = "0.1.0"

from mx_skills.finsearch import query_financial_news
from mx_skills.findata import query_financial_data
from mx_skills.macrodata import query_macro_data
from mx_skills.stockpick import query_stock_pick

__all__ = [
    "query_financial_news",
    "query_financial_data",
    "query_macro_data",
    "query_stock_pick",
    "__version__",
]
