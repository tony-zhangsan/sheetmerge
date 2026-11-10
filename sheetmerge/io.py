"""读写 xlsx / csv，统一成 (headers, rows) 结构。"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Sequence

from openpyxl import Workbook, load_workbook

Table = tuple[list[str], list[list[object]]]


def _clean(value: object) -> object:
    if isinstance(value, str):
        return value.strip()
    return value


def read_table(path: str | Path) -> Table:
    """读取 csv 或 xlsx（第一个工作表），返回表头与数据行。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在：{path}")

    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = list(csv.reader(fh))
        if not reader:
            return [], []
        headers = [_str(h) for h in reader[0]]
        rows = [[_clean(c) for c in row] for row in reader[1:]]
    elif path.suffix.lower() in {".xlsx", ".xlsm"}:
        wb = load_workbook(path, read_only=True, data_only=True)
        ws = wb[wb.sheetnames[0]]
        data = list(ws.iter_rows(values_only=True))
        wb.close()
        if not data:
            return [], []
        headers = [_str(h) for h in data[0]]
        rows = [[_clean(c) for c in row] for row in data[1:]]
    else:
        raise ValueError(f"不支持的格式：{path.suffix}（仅支持 .xlsx / .csv）")

    headers = _strip_tail_empty_head(headers)
    rows = [r[: len(headers)] for r in rows]
    rows = [r for r in rows if any(c not in (None, "") for c in r)]
    return headers, rows


def _str(value: object) -> str:
    return "" if value is None else str(value).strip()


def _strip_tail_empty_head(headers: Sequence[str]) -> list[str]:
    out = list(headers)
    while out and out[-1] == "":
        out.pop()
    return out


def write_table(path: str | Path, headers: Sequence[str], rows: Iterable[Sequence[object]]) -> Path:
    """写出表格，按扩展名决定 xlsx 或 csv。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)

    if path.suffix.lower() == ".csv":
        with path.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(list(headers))
            writer.writerows(rows)
        return path

    wb = Workbook()
    ws = wb.active
    ws.title = "结果"
    ws.append(list(headers))
    for row in rows:
        ws.append(list(row))
    ws.freeze_panes = "A2"
    wb.save(path)
    return path
