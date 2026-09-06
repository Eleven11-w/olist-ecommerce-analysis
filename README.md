# Olist 电商经营分析

> 巴西电商 Olist（Kaggle 公开订单库）经营分析：SQL 多表取数 → 指标体系 → Python 交叉复核 → 业务建议。
> 订单 99,441 笔 / 有效买家 94,983 人 / 数据窗 2016-09 ~ 2018-10。

## 项目简介

用关系型数据库对巴西 Olist 电商 9 万+ 订单做完整经营分析，回答：钱从哪来、客户价值如何、履约质量如何影响体验。全程 SQL 与 Pandas 双口径交叉验证，关键指标口径一致后才进入结论。

覆盖维度：GMV 大盘与月度趋势、区域/品类/支付结构、订单生命周期漏斗、RFM 分层、Cohort 留存、配送时效与差评关系、卖家集中度。

## 关键结论

**1. 履约端整体健康，延迟是差评最强解释变量之一**
已送达率 97.02%（96,478/99,441）；延迟订单占已送达可比单 6.77%。差评率（score≤2）从按时 9.22% 单调升至延迟 8–14 天的 80.08%（95% Wilson CI 各层不重叠），平均分从 4.29 跌到 1.67。

**2. 客户“买完即走”：复购率仅 3.04%，30% GMV 来自高风险价值层**
96.96% 的客户全周期只买 1 单；复购客户 2,887/94,983（3.04%）；首购月 Cohort 第 1 月加权留存 0.45%。RFM 中“高价值流失风险”层 20,922 人贡献 GMV 30.12%。

**3. 需求端区域集中，供给端长尾**
买家 GMV 中 SP 一州占 37.36%，Top5 州合计 73.14%；而 3,053 个卖家中 Top20 仅占 GMV 20.92%，无单一卖家依赖。

**4. 头部品类占约六成，存在“高销量低评分”洼地**
Top10 品类合计 GMV 62.33%；health_beauty 居首（9.14%）；bed_bath_table 订单量最高（9,399）且平均评分在 Top10 中最低（3.98）。

**5. 大促脉冲显著**
月度 GMV 峰值在 2017-11（Black Friday），环比 +53.28%，随后回落 26.50%。

## 可视化

GMV 月度趋势与环比（核心期 2017-01 ~ 2018-08）：

![GMV 月度趋势](results/02_GMV月度趋势.png)

配送延迟与差评率（含 95% Wilson CI）：

![配送延迟差评率](results/analysis_03_配送延迟差评率.png)

## 技术栈与方法

- MySQL 8：建库、9 表导入、8 个必做业务 SQL + 1 个可选 SQL
- Python：Pandas 独立重算关键指标并与 SQL 比对；statsmodels 计算 Wilson 95% CI
- 口径表先于 SQL：GMV / 客单价 / 复购 / Cohort / RFM / 漏斗 / 差评均有书面定义

## 目录结构

```text
olist-project/
├── README.md
├── docs/                  # 数据字典、口径表、业务 memo
├── sql/                   # 00 建表导入；01-08 必做；09 卖家集中度（可选）
├── analysis/              # Python 分析、交叉复核、绘图、一键重跑
└── results/               # 全部 SQL/Python 结果 CSV 与图表
```

## 复现方法

<details>
<summary>展开：数据与运行步骤（本机已配置 MySQL 8.0.46 / conda ds_project）</summary>

原始 CSV 需先按 Kaggle 链接下载到本机（本仓库不含原始数据，脚本内含本机绝对路径 `E:\03_Development\olist-data`，其他机器需同步修改）。

```powershell
# 1) 建库导表（MySQL 重启后如 local_infile 未持久化需先 SET GLOBAL local_infile=1）
mysql --local-infile=1 --default-character-set=utf8mb4 -h127.0.0.1 -P3306 -uroot -p < sql/00_建表导入.sql

# 2) reviews 逐行核对（CSV vs MySQL）
$env:MYSQL_PWD='你的密码'
python analysis/import_qc.py

# 3) 一键重跑 01-09 并导出结果 CSV
python analysis/run_all_sql.py

# 4) Python 数据质量 / 交叉复核 / 专题
python analysis/01_数据质量.py
python analysis/02_关键指标复核.py
python analysis/03_专题分析.py

# 5) 出图（本机 ds_project 的 matplotlib savefig 存在环境问题，暂用 base 环境绘图）
python analysis/02_plot_trend.py
python analysis/03_plot_delay.py
```

关键环境：conda `ds_project`（Python 3.12、pandas 2.3.3、numpy 2.5.2、scipy 1.18.0、statsmodels 0.15.0、pymysql 1.2.0）。
</details>

## 口径要点（完整版见 docs/口径表.md）

| 指标 | 口径 |
|---|---|
| 统计范围 | 2016-09-04 ~ 2018-10-17 |
| GMV | Σ(price+freight)，剔除 canceled/unavailable；items 口径 R$15,735,527.03，与 payments 合计差 R$3,609.98（0.02%）已写明 |
| 订单量/买家 | 有商品明细的有效订单 98,199；买家按 customer_unique_id 去重 94,983 |
| 复购率 | 全周期 ≥2 单客户占比 3.04% |
| Cohort 留存 | 首购月 cohort，第 n 月任意有效订单回访比例；矩阵已补零 |
| RFM | R≤197/339 天、M≤R$75.25/R$152.09 分档；F=复购（≥2 单） |
| 漏斗 | 正向序列 created→…→delivered；canceled/unavailable 单列 |
| 差评/延迟 | score≤2；已送达且日期完整订单，每单一评 |

## 局限与边界

- 巴西市场数据：方法可迁移，数值不直接照搬到中国市场。
- 结论为描述性相关/分层差异，不做因果推断。
- 评价正文缺失率高（标题 88%、正文 59%），评分字段覆盖完整。
- 数据首尾月份样本稀疏（2017-01 前、2018-09 后），趋势结论以 2017-01 ~ 2018-08 为核心期。
- 发现 61 单送达早于审批的录入异常（0.06%），未对主结论构成影响。