"""核心算法：合并、去重、匹配、汇总。全部为纯函数，便于测试。"""

from __future__ import annotations

from typing import Iterable, Sequence

Row = list[object]


def merge_rows(
    tables: Sequence[tuple[list[str], list[list[object]]]],
    source_names: Sequence[str] | None = None,
    add_source: bool = False,
) -> tuple[list[str], list[Row]]:
    """按表头名对齐后纵向合并多张表；缺列补空，多余列进并集。"""
    headers: list[str] = []
    for table_headers, _ in tables:
        for name in table_headers:
            if name not in headers:
                headers.append(name)

    out_headers = (["来源文件"] if add_source else []) + headers
    out_rows: list[Row] = []

    for index, (table_headers, rows) in enumerate(tables):
        position = {name: i for i, name in enumerate(table_headers)}
        source = ""
        if add_source:
            source = source_names[index] if source_names and index < len(source_names) else str(index + 1)
        for row in rows:
            record: Row = []
            for name in headers:
                idx = position.get(name)
                record.append(row[idx] if idx is not None and idx < len(row) else None)
            if add_source:
                record.insert(0, source)
            out_rows.append(record)

    return out_headers, out_rows


def _key_of(row: Row, headers: Sequence[str], keys: Sequence[str]) -> tuple[str, ...]:
    position = {name: i for i, name in enumerate(headers)}
    values: list[str] = []
    for key in keys:
        idx = position[key]
        value = row[idx] if idx < len(row) else None
        values.append("" if value is None else str(value).strip())
    return tuple(values)


def dedup_rows(
    headers: Sequence[str],
    rows: Sequence[Row],
    keys: Sequence[str],
    keep: str = "first",
) -> tuple[list[Row], list[Row]]:
    """按 keys 去重，返回 (保留行, 被剔除的重复行)。keep 支持 first / last。"""
    missing = [k for k in keys if k not in headers]
    if missing:
        raise KeyError(f"去重列不存在：{', '.join(missing)}")

    buckets: dict[tuple[str, ...], list[Row]] = {}
    order: list[tuple[str, ...]] = []
    for row in rows:
        key = _key_of(row, headers, keys)
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(row)

    kept: list[Row] = []
    dropped: list[Row] = []
    for key in order:
        group = buckets[key]
        if keep == "last":
            kept.append(group[-1])
            dropped.extend(group[:-1])
        else:
            kept.append(group[0])
            dropped.extend(group[1:])
    return kept, dropped


def match_rows(
    left_headers: Sequence[str],
    left_rows: Sequence[Row],
    right_headers: Sequence[str],
    right_rows: Sequence[Row],
    key_left: str,
    key_right: str,
    suffix: str = "_右表",
) -> tuple[list[str], list[Row], list[Row]]:
    """左连接匹配；返回 (结果表头, 结果行, 未匹配的左表行)。"""
    for name in (key_left,):
        if name not in left_headers:
            raise KeyError(f"左表缺少列：{name}")
    if key_right not in right_headers:
        raise KeyError(f"右表缺少列：{key_right}")

    right_position = {name: i for i, name in enumerate(right_headers)}
    right_index: dict[str, Row] = {}
    for row in right_rows:
        idx = right_position[key_right]
        value = row[idx] if idx < len(row) else None
        key = "" if value is None else str(value).strip()
        if key and key not in right_index:
            right_index[key] = row

    extra_headers = [name for name in right_headers if name != key_right]
    renamed = [
        name if name not in left_headers else f"{name}{suffix}" for name in extra_headers
    ]
    out_headers = list(left_headers) + renamed + ["匹配状态"]

    left_position = {name: i for i, name in enumerate(left_headers)}
    out_rows: list[Row] = []
    unmatched: list[Row] = []

    for row in left_rows:
        idx = left_position[key_left]
        value = row[idx] if idx < len(row) else None
        key = "" if value is None else str(value).strip()
        hit = right_index.get(key) if key else None
        record: Row = list(row)
        if hit is None:
            record.extend([None] * len(renamed))
            record.append("未匹配")
            unmatched.append(list(row))
        else:
            for name in extra_headers:
                idx2 = right_position[name]
                record.append(hit[idx2] if idx2 < len(hit) else None)
            record.append("已匹配")
        out_rows.append(record)

    return out_headers, out_rows, unmatched


def _to_number(value: object) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").replace("￥", "").replace("¥", "").strip()
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    try:
        return float(text)
    except ValueError:
        return None


def summarize_rows(
    headers: Sequence[str],
    rows: Sequence[Row],
    group_by: Sequence[str],
    value_cols: Sequence[str] | None = None,
) -> tuple[list[str], list[Row]]:
    """按 group_by 分组，输出记录数与各数值列合计。"""
    position = {name: i for i, name in enumerate(headers)}
    for name in group_by:
        if name not in position:
            raise KeyError(f"分组列不存在：{name}")
    value_cols = list(value_cols or [])
    for name in value_cols:
        if name not in position:
            raise KeyError(f"汇总列不存在：{name}")

    groups: dict[tuple[str, ...], dict[str, float]] = {}
    counts: dict[tuple[str, ...], int] = {}
    order: list[tuple[str, ...]] = []

    for row in rows:
        key = tuple(
            "" if (row[position[name]] is None) else str(row[position[name]]).strip()
            for name in group_by
        )
        if key not in groups:
            groups[key] = {name: 0.0 for name in value_cols}
            counts[key] = 0
            order.append(key)
        counts[key] += 1
        for name in value_cols:
            number = _to_number(row[position[name]])
            if number is not None:
                groups[key][name] += number

    out_headers = list(group_by) + ["记录数"] + [f"{name}合计" for name in value_cols]
    out_rows: list[Row] = []
    for key in order:
        record: Row = list(key) + [counts[key]]
        for name in value_cols:
            record.append(round(groups[key][name], 2))
        out_rows.append(record)
    return out_headers, out_rows
