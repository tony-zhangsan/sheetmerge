# sheetmerge

轻量表格合并、去重、匹配与汇总工具。面向「每个月都要手工合并十几张 Excel」的运营和财务场景，用一条命令代替复制粘贴。

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-unittest-brightgreen)

## 为什么做这个

日常表格处理有四件事最耗时间，而且每次都要重做一遍：

1. 多张同结构的表要合并（区域表、月表、门店表），列顺序经常不一致；
2. 合并后要按业务主键去重，还要知道被删掉的是哪几行；
3. 两张表要按客户名/订单号匹配，最麻烦的是找出**对不上的那些行**；
4. 最后按客户或月份出一张汇总表。

`sheetmerge` 把这四件事做成四个子命令，输入输出都是 `.xlsx` / `.csv`，不需要装 Excel，也不依赖 pandas。

## 安装

```bash
pip install openpyxl
git clone https://github.com/<your-name>/sheetmerge.git
cd sheetmerge
python -m sheetmerge --version
```

也可以直接 `pip install -e .` 安装命令行入口。

## 四个子命令

### 1. merge：按表头名对齐后合并

```bash
python -m sheetmerge merge examples/sample/订单_华东.xlsx examples/sample/订单_华南.xlsx \
    -o examples/out/订单_合并.xlsx --source
```

- 按**列名**对齐，列顺序不同也能合；缺列补空，多的列进并集；
- `--source` 增加「来源文件」列，方便追溯每一行来自哪张表。

### 2. dedup：按键列去重并导出重复清单

```bash
python -m sheetmerge dedup examples/out/订单_合并.xlsx --keys 订单号 \
    -o examples/out/订单_去重.xlsx --duplicates examples/out/订单_重复行.xlsx
```

- 键值会先 `strip()`，避免「云海贸易 」和「云海贸易」被当成两个客户；
- `--keep last` 保留最后一条；被剔除的行可以单独存一张表。

### 3. match：两张表左连接匹配，并输出未匹配清单

```bash
python -m sheetmerge match --left examples/out/订单_去重.xlsx \
    --right examples/sample/客户名单.xlsx \
    --key-left 客户名称 --key-right 客户名称 \
    -o examples/out/订单_带客户信息.xlsx --unmatched examples/out/未匹配客户.xlsx
```

- 结果表最后一列是「匹配状态」（已匹配 / 未匹配）；
- 右表与左表重名的列自动加 `_右表` 后缀，不会覆盖原始数据；
- `--unmatched` 单独输出左表中没匹配上的行，这是对账时最需要的清单。

### 4. report：按分组列出汇总

```bash
python -m sheetmerge report examples/out/订单_带客户信息.xlsx \
    --group-by 区域 --value 金额 -o examples/out/区域汇总.xlsx
```

- 数值列支持 `1,000`、`￥100`、`(100)` 这类文本写法；
- 输出「记录数 + 各数值列合计」，可直接贴进周报。

## 示例数据

```bash
python examples/make_samples.py     # 生成两份区域订单表 + 一份客户名单
```

示例数据包含一条刻意的重复订单（SO-1006）和一个不在客户名单里的客户，用来演示去重与未匹配清单。

## 目录结构

```
sheetmerge/
├── sheetmerge/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py          # argparse 子命令与输出
│   ├── core.py         # 合并 / 去重 / 匹配 / 汇总（纯函数）
│   └── io.py           # xlsx、csv 读写
├── tests/test_core.py  # 11 个单元测试
├── examples/make_samples.py
├── .github/workflows/ci.yml
├── pyproject.toml
└── LICENSE
```

## 测试

```bash
python -m unittest discover -s tests -v
```

CI 在 Ubuntu 与 Windows 上跑 3.10 / 3.11 / 3.12 三个版本。

## 边界与已知限制

- 只读每个工作簿的**第一个工作表**；多 sheet 需要先拆分；
- 不处理合并单元格、公式计算（读取的是缓存值，`data_only=True`）；
- 大文件走 `read_only=True` 流式读取，但汇总仍在内存中完成，百万行级别建议先分片；
- 匹配是「左连接 + 首个命中」，右表出现重复键时只取第一条，重复键需要先用 `dedup` 处理。

## 路线图

- [ ] 支持指定 sheet 名称与多 sheet 合并
- [ ] 增加 `--encoding` 参数处理 GBK 编码的 CSV
- [ ] 输出 Excel 数据透视表而非静态汇总
- [ ] 支持按正则表达式清洗字段

## License

MIT
