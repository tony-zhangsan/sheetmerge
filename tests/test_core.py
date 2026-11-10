from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sheetmerge.core import dedup_rows, match_rows, merge_rows, summarize_rows
from sheetmerge.io import read_table, write_table


class MergeTest(unittest.TestCase):
    def test_align_headers_and_fill_missing(self) -> None:
        left = (["订单号", "金额"], [["SO-1", 100], ["SO-2", 200]])
        right = (["订单号", "金额", "状态"], [["SO-3", 300, "已出库"]])
        headers, rows = merge_rows([left, right])
        self.assertEqual(headers, ["订单号", "金额", "状态"])
        self.assertEqual(rows[0], ["SO-1", 100, None])
        self.assertEqual(rows[2], ["SO-3", 300, "已出库"])

    def test_add_source_column(self) -> None:
        left = (["订单号"], [["SO-1"]])
        right = (["订单号"], [["SO-2"]])
        headers, rows = merge_rows([left, right], ["华东.xlsx", "华南.xlsx"], add_source=True)
        self.assertEqual(headers[0], "来源文件")
        self.assertEqual([r[0] for r in rows], ["华东.xlsx", "华南.xlsx"])


class DedupTest(unittest.TestCase):
    def test_remove_duplicates_and_keep_first(self) -> None:
        headers = ["订单号", "金额"]
        rows = [["SO-1", 100], ["SO-1", 100], ["SO-2", 200]]
        kept, dropped = dedup_rows(headers, rows, ["订单号"])
        self.assertEqual(len(kept), 2)
        self.assertEqual(len(dropped), 1)

    def test_key_is_trimmed(self) -> None:
        headers = ["客户名称"]
        rows = [["  云海贸易 "], ["云海贸易"]]
        kept, dropped = dedup_rows(headers, rows, ["客户名称"])
        self.assertEqual(len(kept), 1)
        self.assertEqual(len(dropped), 1)

    def test_missing_key_raises(self) -> None:
        with self.assertRaises(KeyError):
            dedup_rows(["订单号"], [["SO-1"]], ["不存在的列"])


class MatchTest(unittest.TestCase):
    def test_left_join_reports_unmatched(self) -> None:
        left_headers = ["订单号", "客户名称"]
        left_rows = [["SO-1", "云海贸易"], ["SO-2", "未知客户"]]
        right_headers = ["客户名称", "区域"]
        right_rows = [["云海贸易", "华东"]]
        headers, rows, unmatched = match_rows(
            left_headers, left_rows, right_headers, right_rows, "客户名称", "客户名称"
        )
        self.assertEqual(headers, ["订单号", "客户名称", "区域", "匹配状态"])
        self.assertEqual(rows[0][2], "华东")
        self.assertEqual(rows[1][-1], "未匹配")
        self.assertEqual(len(unmatched), 1)

    def test_conflicting_column_is_renamed(self) -> None:
        headers, rows, _ = match_rows(
            ["客户名称"], [["A"]], ["客户名称", "区域"], [["A", "华东"]], "客户名称", "客户名称"
        )
        self.assertIn("区域", headers)
        self.assertEqual(rows[0][-1], "已匹配")


class SummarizeTest(unittest.TestCase):
    def test_sum_and_count(self) -> None:
        headers = ["客户名称", "金额"]
        rows = [["A", 100], ["A", "200.5"], ["B", "1,000"]]
        out_headers, out_rows = summarize_rows(headers, rows, ["客户名称"], ["金额"])
        self.assertEqual(out_headers, ["客户名称", "记录数", "金额合计"])
        self.assertEqual(out_rows[0], ["A", 2, 300.5])
        self.assertEqual(out_rows[1], ["B", 1, 1000.0])


class IOTest(unittest.TestCase):
    def test_xlsx_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "demo.xlsx"
            write_table(path, ["订单号", "金额"], [["SO-1", 100], ["SO-2", None]])
            headers, rows = read_table(path)
            self.assertEqual(headers, ["订单号", "金额"])
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0], ["SO-1", 100])

    def test_csv_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "demo.csv"
            write_table(path, ["客户名称", "区域"], [["云海贸易", "华东"]])
            headers, rows = read_table(path)
            self.assertEqual(headers, ["客户名称", "区域"])
            self.assertEqual(rows, [["云海贸易", "华东"]])

    def test_unsupported_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "demo.txt"
            path.write_text("x", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_table(path)


if __name__ == "__main__":
    unittest.main()
