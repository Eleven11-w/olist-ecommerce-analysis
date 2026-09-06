# 项目 A：电商经营分析（Olist）

> 目标依据：《数据分析实习生_简历补强计划_优化版.md》M1 / 《项目操作手册》§2。
> 状态：8 个必做 SQL + 1 个可选 SQL 完成；SQL/Python 交叉复核通过；memo 已成文。
> 待办：5 分钟脱稿讲解录音、GitHub 仓库推送。

## 数据来源

- Kaggle：`olistbr/brazilian-ecommerce`（约 10 万订单、8 张核心表 + 1 张品类翻译表）
- 下载链接：<https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce>
- 本机原始 CSV：`E:\03_Development\olist-data`（不入库不入 GitHub）

## 目录结构

```text
olist-project/
├── README.md      # 运行顺序、复现方法、关键数字基线（本文档）
├── docs/
│   ├── 数据字典.md
│   ├── 口径表.md
│   └── 业务结论文档.md   # memo
├── sql/           # 00 建表导入；01-08 必做；09 卖家集中度（可选）
├── analysis/      # 01 数据质量 / 02 关键指标复核 / 03 专题分析 + 绘图与通用导出
├── results/       # SQL 与 Python 输出的 CSV、PNG
└── .gitignore
```

## 复现方法

前置：MySQL 服务运行中；root 密码由本人保管；原始 CSV 在 `E:\03_Development\olist-data`。

1. 从零重建库表并导入（脚本会 DROP 重建 9 张表；MySQL 重启后需先执行 `SET GLOBAL local_infile=1;`）：

```powershell
mysql --local-infile=1 --default-character-set=utf8mb4 -h127.0.0.1 -P3306 -uroot -p < sql/00_建表导入.sql
```

2. 逐行核对 reviews 是否与 CSV 一致（Pandas）：

```powershell
$env:MYSQL_PWD='你的密码'
& 'E:\03_Development\Anaconda\envs\ds_project\python.exe' 'E:\03_Development\DataAnalyst\olist-project\analysis\import_qc.py'
```

3. 批量重跑 01–09 分析 SQL 并写结果 CSV（`run_sql_export.py` 只执行 SELECT）：

```powershell
$env:MYSQL_PWD='你的密码'
& 'E:\03_Development\Anaconda\envs\ds_project\python.exe' 'E:\03_Development\DataAnalyst\olist-project\analysis\run_all_sql.py'
```

4. 运行 Python 分析（数据质量/复核/专题；专题图用 base 环境画，见下）：

```powershell
$env:MYSQL_PWD='你的密码'
& 'E:\03_Development\Anaconda\envs\ds_project\python.exe' 'E:\03_Development\DataAnalyst\olist-project\analysis\01_数据质量.py'
& 'E:\03_Development\Anaconda\envs\ds_project\python.exe' 'E:\03_Development\DataAnalyst\olist-project\analysis\02_关键指标复核.py'
& 'E:\03_Development\Anaconda\envs\ds_project\python.exe' 'E:\03_Development\DataAnalyst\olist-project\analysis\03_专题分析.py'
# 绘图（base 环境；ds_project 的 matplotlib 保存图片会崩溃，暂用 base）
& 'E:\03_Development\Anaconda\python.exe' 'E:\03_Development\DataAnalyst\olist-project\analysis\02_plot_trend.py'
& 'E:\03_Development\Anaconda\python.exe' 'E:\03_Development\DataAnalyst\olist-project\analysis\03_plot_delay.py'
```

5. 比对下方“关键数字基线”，不一致即未达标。

## 本机环境记录（2026-09-06）

| 项目 | 状态与位置 |
|---|---|
| MySQL 8.0.46 | Windows 服务 `MySQL`（开机自启），配置 `E:\03_Development\MySQL\my.ini`，数据目录 `E:\03_Development\MySQL\data`，仅监听 127.0.0.1:3306；my.ini 已加 `local_infile=ON`（重启服务后无需再手动 SET GLOBAL） |
| conda 环境 | `ds_project` @ `E:\03_Development\Anaconda\envs\ds_project`（Python 3.12） |
| 关键包版本 | pandas 2.3.3 / numpy 2.5.2 / scipy 1.18.0 / statsmodels 0.15.0 / sqlalchemy 2.0.52 / pymysql 1.2.0 / matplotlib 3.9.2 |
| matplotlib 已知问题 | ds_project 内 savefig 崩溃（含 SVG）；绘图暂时用 base 环境 `E:\03_Development\Anaconda\python.exe` |

## 关键数字基线（SQL 已跑通；改口径必须同步更新 SQL/Python/README/memo）

| 指标 | 数字 | 口径版本 | 核对方式 |
|---|---|---|---|
| 数据时间窗 | 2016-09-04 ~ 2018-10-17 | 见 docs/口径表.md | SQL min/max |
| 订单总量 | 99,441（orders 全部行数） | 见 docs/口径表.md | SQL COUNT |
| 有效订单量（有 items） | 98,199 | 见 docs/口径表.md | SQL vs Python |
| GMV（items 口径） | R$15,735,527.03 | 见 docs/口径表.md | 与 payments 核对：R$15,739,137.01（差 R$3,609.98，0.02%） |
| 买家数 | 94,983（customer_unique_id 去重，须有商品明细） | 见 docs/口径表.md | SQL vs Python |
| 客单价 | R$160.24 | GMV ÷ 有 items 的有效订单量 | SQL vs Python |
| 复购率 | 3.04%（2,887/94,983，全周期 ≥2 单） | 按 customer_unique_id | SQL6/7 vs Python |
| GMV 月度峰值 | R$1,172,191.68（2017-11，环比 +53.28%） | 核心期 2017-01~2018-08 | SQL2，首尾稀疏月除外 |
| GMV 区域集中度 | SP 37.36%；Top3(SP/RJ/MG) 62.51%；Top5 73.14% | 买家州 × items GMV | SQL3，各州合计=SQL1 GMV |
| 支付结构 | credit_card 78.47% / boleto 17.96% / voucher 2.22% / debit_card 1.35% | payment_value 口径 | SQL3，合计=payments GMV |
| 品类 Top10 | Top1 health_beauty 占 9.14%；Top10 合计 62.33%；bed_bath_table 订单量最高且平均评分 Top10 最低 3.98 | items GMV × 品类 × 订单-品类评分 | SQL4 |
| 生命周期漏斗 | created 98,207 → delivered 96,478（全单口径 97.02%）；最大单环节流失 shipped→delivered 1,107；终态 canceled 625 + unavailable 609 | 正向状态序列，canceled/unavailable 单列 | SQL5 |
| RFM 分层 | 阈值：R≤197/339 天；M≤R$75.25/R$152.09；F=复购(≥2 单)。高价值流失风险 20,922 人/占GMV 30.12%；近期高价值新客 20,385 人/28.82%；核心复购价值 1,005 人/2.15% | 显式数值阈值，见 results/06_RFM分层_q2.csv | SQL6 |
| Cohort 留存 | 23 个首购月客群；第1月加权留存 0.45%，第3月 0.26%；矩阵已补零到数据末日，其中 2 个微小客群(<30)需谨慎解读 | customer_unique_id 首购月 Cohort | SQL7 |
| 配送延迟 vs 差评 | 延迟率 6.77%（6,534/96,470）；按时差评率 9.22%均分4.29；延迟8-14天差评率80.08%均分1.67 | 已送达订单，差评score<=2，每单一评 | SQL8 |
| 卖家集中度（可选） | 活跃卖家 3,053；Top1 1.58%、Top5 7.39%、Top10 12.86%、Top20 20.92%（长尾明显） | 有效订单 × items GMV，按 seller_id | SQL9 |

## Gate A 检查清单（进度跟踪）

- [x] 8+ 个 SQL 脚本全部可重跑（01-08；09 可选），结果 CSV 在 `results/`，README 记录关键数字基线
- [x] 数据字典 + 口径表成文，每个指标能 1 句话讲清
- [x] SQL 与 Python 重算的 3 个关键指标完全一致（GMV/买家数/复购率；analysis/02）
- [x] memo 有 3+ 条带数字证据的建议，每条都有“观测→归因→建议→验证”
- [ ] 能脱稿讲 5 分钟：目标 → 数据与口径 → 3 个发现 → 1 个建议（录音听一遍）
- [ ] GitHub 仓库结构清晰、README 含运行命令（原始 CSV 不提交）

## 硬规则

- 每个写进简历的数字必须能 1 句话讲清口径；说不清就删。
- 原始数据、MySQL 密码、Kaggle 账号信息不进仓库。
- 数字对不上先查口径，SQL/Python/README/memo 四方必须一致；不许为“好看”改口径删样本。
- 评价类分析注意：同一订单同品类多件商品只计一条评分（订单-品类粒度）。