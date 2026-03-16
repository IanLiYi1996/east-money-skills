"""Unified CLI entry point for mx-skills."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys


def _run_async(coro):
    """Run an async coroutine from sync CLI context."""
    return asyncio.run(coro)


def _cmd_finsearch(args):
    from pathlib import Path

    from mx_skills.finsearch import query_financial_news

    out_dir = Path(args.output_dir) if args.output_dir else None
    result = _run_async(query_financial_news(
        query=args.query,
        output_dir=out_dir,
        save_to_file=not args.no_save,
    ))
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(2)
    if result.get("output_path"):
        print(f"Saved: {result['output_path']}")
    print(result.get("content", ""))


def _cmd_findata(args):
    from pathlib import Path

    from mx_skills.findata import query_financial_data

    out_dir = Path(args.output_dir) if args.output_dir else None
    result = _run_async(query_financial_data(query=args.query, output_dir=out_dir))
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(2)
    print(f"File: {result['file_path']}")
    print(f"Description: {result['description_path']}")
    print(f"Rows: {result['row_count']}")


def _cmd_macro(args):
    from pathlib import Path

    from mx_skills.macrodata import query_macro_data

    out_dir = Path(args.output_dir) if args.output_dir else None
    result = _run_async(query_macro_data(query=args.query, output_dir=out_dir))
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(2)
    print(f"CSV: {result['csv_paths']}")
    print(f"Description: {result['description_path']}")
    print(f"Rows: {result['row_counts']}")


def _cmd_stockpick(args):
    from pathlib import Path

    from mx_skills.stockpick import query_stock_pick

    out_dir = Path(args.output_dir) if args.output_dir else None
    result = _run_async(query_stock_pick(
        query=args.query,
        select_type=args.type,
        output_dir=out_dir,
    ))
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(2)
    print(f"CSV: {result['csv_path']}")
    print(f"Description: {result['description_path']}")
    print(f"Rows: {result['row_count']}")


def main():
    parser = argparse.ArgumentParser(
        prog="mx-skills",
        description="East Money MiaoXiang Financial Skills CLI",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable debug logging",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # finsearch
    p_fin = subparsers.add_parser("finsearch", help="Search financial news and research")
    p_fin.add_argument("query", help="Natural language query")
    p_fin.add_argument("--output-dir", help="Output directory")
    p_fin.add_argument("--no-save", action="store_true", help="Don't save to file")
    p_fin.set_defaults(func=_cmd_finsearch)

    # findata
    p_data = subparsers.add_parser("findata", help="Query financial data")
    p_data.add_argument("query", help="Natural language query")
    p_data.add_argument("--output-dir", help="Output directory")
    p_data.set_defaults(func=_cmd_findata)

    # macro
    p_macro = subparsers.add_parser("macro", help="Query macro economic data")
    p_macro.add_argument("query", help="Natural language query")
    p_macro.add_argument("--output-dir", help="Output directory")
    p_macro.set_defaults(func=_cmd_macro)

    # stockpick
    p_stock = subparsers.add_parser("stockpick", help="Screen stocks/funds/sectors")
    p_stock.add_argument("query", help="Natural language screening criteria")
    p_stock.add_argument(
        "--type", required=True,
        choices=["A股", "港股", "美股", "基金", "ETF", "可转债", "板块"],
        help="Security type to screen",
    )
    p_stock.add_argument("--output-dir", help="Output directory")
    p_stock.set_defaults(func=_cmd_stockpick)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s %(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)

    args.func(args)


if __name__ == "__main__":
    main()
