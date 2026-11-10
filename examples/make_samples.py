"""生成演示用示例数据：两份分区域订单表 + 一份客户名单。"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

HERE = Path(__file__).resolve().parent
OUT = HERE / "sample"

EAST = [
    ["SO-1001", "苏州云海贸易", "2026-10-02", "收纳盒", 12, 39.9, 478.8, "已出库"],
    ["SO-1002", "杭州千帆电商", "2026-10-03", "桌面置物架", 8, 69.0, 552.0, "已出库"],
    ["SO-1003", "宁波恒达百货", "2026-10-05", "收纳盒", 24, 39.9, 957.6, "待出库"],
    ["SO-1004", "苏州云海贸易", "2026-10-07", "折叠衣架", 30, 19.5, 585.0, "已出库"],
    ["SO-1005", "上海禾木生活", "2026-10-09", "桌面置物架", 15, 69.0, 1035.0, "已出库"],
]

SOUTH = [
    ["SO-1006", "广州南沙优选", "2026-10-04", "收纳盒", 18, 39.9, 718.2, "已出库"],
    ["SO-1007", "深圳前海严选", "2026-10-06", "折叠衣架", 40, 19.5, 780.0, "待出库"],
    ["SO-1008", "广州南沙优选", "2026-10-08", "桌面置物架", 10, 69.0, 690.0, "已出库"],
    ["SO-1009", "佛山顺联批发", "2026-10-10", "收纳盒", 22, 39.9, 877.8, "已出库"],
    ["SO-1006", "广州南沙优选", "2026-10-04", "收纳盒", 18, 39.9, 718.2, "已出库"],
]

CUSTOMERS = [
    ["苏州云海贸易", "华东", "张敏", "款到发货"],
    ["杭州千帆电商", "华东", "李伟", "月结30天"],
    ["宁波恒达百货", "华东", "王芳", "款到发货"],
    ["上海禾木生活", "华东", "陈晨", "月结60天"],
    ["广州南沙优选", "华南", "刘洋", "月结30天"],
    ["深圳前海严选", "华南", "赵磊", "款到发货"],
    ["东莞优品仓", "华南", "周静", "月结30天"],
]

ORDER_HEADERS = ["订单号", "客户名称", "下单日期", "商品", "数量", "单价", "金额", "状态"]
CUSTOMER_HEADERS = ["客户名称", "区域", "跟单员", "结算方式"]


def write(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "明细"
    ws.append(headers)
    for row in rows:
        ws.append(row)
    ws.freeze_panes = "A2"
    wb.save(path)
    print(f"已生成 {path.name}：{len(rows)} 行")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write(OUT / "订单_华东.xlsx", ORDER_HEADERS, EAST)
    write(OUT / "订单_华南.xlsx", ORDER_HEADERS, SOUTH)
    write(OUT / "客户名单.xlsx", CUSTOMER_HEADERS, CUSTOMERS)


if __name__ == "__main__":
    main()
