"""命令行入口：merge / dedup / match / report。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .core import dedup_rows, match_rows, merge_rows, summarize_rows
from .io import read_table, write_table


def _split(text: str | None) -> list[str]:
    if not text:
        return []
    return [part.strip() for part in text.replace("，", ",").split(",") if part.strip()]


def cmd_merge(args: argparse.Namespace) -> int:
    tables = [read_table(p) for p in args.inputs]
    names = [Path(p).name for p in args.inputs]
    headers, rows = merge_rows(tables, source_names=names, add_source=args.source)
    write_table(args.output, headers, rows)
    print(f"合并完成：{len(tables)} 个文件 → {len(rows)} 行 / {len(headers)} 列")
    print(f"输出：{args.output}")
    return 0


def cmd_dedup(args: argparse.Namespace) -> int:
    headers, rows = read_table(args.input)
    kept, dropped = dedup_rows(headers, rows, _split(args.keys), keep=args.keep)
    write_table(args.output, headers, kept)
    print(f"去重完成：原始 {len(rows)} 行 → 保留 {len(kept)} 行，剔除重复 {len(dropped)} 行")
    print(f"输出：{args.output}")
    if args.duplicates:
        write_table(args.duplicates, headers, dropped)
        print(f"重复清单：{args.duplicates}")
    return 0


def cmd_match(args: argparse.Namespace) -> int:
    left_headers, left_rows = read_table(args.left)
    right_headers, right_rows = read_table(args.right)
    headers, rows, unmatched = match_rows(
        left_headers,
        left_rows,
        right_headers,
        right_rows,
        key_left=args.key_left,
        key_right=args.key_right,
    )
    write_table(args.output, headers, rows)
    hit = len(rows) - len(unmatched)
    print(f"匹配完成：左表 {len(left_rows)} 行，已匹配 {hit} 行，未匹配 {len(unmatched)} 行")
    print(f"输出：{args.output}")
    if args.unmatched:
        write_table(args.unmatched, left_headers, unmatched)
        print(f"未匹配清单：{args.unmatched}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    headers, rows = read_table(args.input)
    out_headers, out_rows = summarize_rows(
        headers, rows, _split(args.group_by), _split(args.value)
    )
    write_table(args.output, out_headers, out_rows)
    print(f"汇总完成：{len(rows)} 行 → {len(out_rows)} 个分组")
    print(f"输出：{args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sheetmerge",
        description="表格合并、去重、匹配与汇总（支持 .xlsx / .csv）",
    )
    parser.add_argument("--version", action="version", version=f"sheetmerge {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_merge = sub.add_parser("merge", help="按表头对齐后合并多个表")
    p_merge.add_argument("inputs", nargs="+", help="待合并的文件")
    p_merge.add_argument("-o", "--output", required=True, help="输出文件")
    p_merge.add_argument("--source", action="store_true", help="增加“来源文件”列")
    p_merge.set_defaults(func=cmd_merge)

    p_dedup = sub.add_parser("dedup", help="按键列去重并输出重复清单")
    p_dedup.add_argument("input", help="输入文件")
    p_dedup.add_argument("--keys", required=True, help="键列，逗号分隔")
    p_dedup.add_argument("-o", "--output", required=True, help="去重后输出")
    p_dedup.add_argument("--duplicates", help="重复行清单输出")
    p_dedup.add_argument("--keep", choices=["first", "last"], default="first")
    p_dedup.set_defaults(func=cmd_dedup)

    p_match = sub.add_parser("match", help="两张表按键列左连接匹配")
    p_match.add_argument("--left", required=True, help="左表")
    p_match.add_argument("--right", required=True, help="右表")
    p_match.add_argument("--key-left", required=True, help="左表键列")
    p_match.add_argument("--key-right", required=True, help="右表键列")
    p_match.add_argument("-o", "--output", required=True, help="匹配结果输出")
    p_match.add_argument("--unmatched", help="未匹配记录输出")
    p_match.set_defaults(func=cmd_match)

    p_report = sub.add_parser("report", help="按分组列生成汇总表")
    p_report.add_argument("input", help="输入文件")
    p_report.add_argument("--group-by", required=True, help="分组列，逗号分隔")
    p_report.add_argument("--value", help="需要合计的数值列，逗号分隔")
    p_report.add_argument("-o", "--output", required=True, help="汇总表输出")
    p_report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
