# Olist 电商经营分析 · 项目 A 完整操作说明

> 巴西电商 Olist（Kaggle 公开订单库）经营分析：MySQL 多表取数 → SQL 业务分析 → Pandas 交叉复核 → 图表与业务 memo。
> 覆盖订单 99,441 笔 / 有效买家 94,983 人 / 数据窗 2016-09-04 ~ 2018-10-17。

本文档既是项目展示页，也是从零复现的完整操作手册：所有数据库操作指令、Python 指令、运行注释、输出结果均按真实执行顺序记录。

---

## 1. 项目简介

项目目标：用关系型数据库对巴西 Olist 电商约 9.9 万订单做完整经营分析，回答三个问题：

1. 钱从哪来——GMV 规模、月度趋势、区域 / 品类 / 支付结构；
2. 客户价值如何——复购、首购月 Cohort 留存、RFM 分层；
3. 履约质量如何影响体验——配送延迟与差评率的关系。

所有关键指标先用 SQL 计算，再用 Pandas 独立重算交叉验证，数字一致后才进入业务结论。

---

## 2. 数据与表结构

- 来源：[Kaggle · Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- 仓库 `data/` 收录 9 张原始 CSV，合计约 120 MB
- 许可：Kaggle 数据集页面未标注明确 License；本项目仅作学习与展示，公开再分发请保留来源与归属

| 官方 CSV | 表名 | 行数 | 主键 / 重复检查 |
|---|---|---:|---|
| olist_orders_dataset.csv | orders | 99,441 | order_id 唯一 |
| olist_order_items_dataset.csv | order_items | 112,650 | (order_id, order_item_id) 唯一 |
| olist_order_payments_dataset.csv | order_payments | 103,886 | (order_id, payment_sequential) 唯一 |
| olist_order_reviews_dataset.csv | order_reviews | 99,224 | review_id 重复 814 行，改用自增 id |
| olist_customers_dataset.csv | customers | 99,441 | customer_id 唯一；unique_id 96,096 |
| olist_sellers_dataset.csv | sellers | 3,095 | seller_id 唯一 |
| olist_products_dataset.csv | products | 32,951 | product_id 唯一 |
| olist_geolocation_dataset.csv | geolocation | 1,000,163 | 无主键，zip 前缀加索引 |
| product_category_name_translation.csv | product_category_name_translation | 71 | category 唯一 |

---

## 3. 环境清单

| 组件 | 版本 / 路径 |
|---|---|
| MySQL | 8.0.46，服务名 `MySQL`，根目录 `E:\03_Development\MySQL` |
| conda 环境 | `ds_project`：`E:\03_Development\Anaconda\envs\ds_project` |
| Python | 3.12（conda-forge） |
| 依赖 | pandas 2.3.3、numpy 2.5.2、scipy 1.18.0、statsmodels 0.15.0、matplotlib 3.9.2、pymysql 1.2.0 |
| 依赖清单 | `requirements.txt` |

本机 BLAS 为 MKL。若 ds_project 环境绘图/矩阵运算崩溃（异常码 `0xc06d007f`），请确认 `MKL_THREADING_LAYER=TBB`；conda 激活脚本与绘图脚本均已内置该设置。

---

## 4. 目录结构

```text
olist-project/
├── README.md                # 本文档：展示 + 完整操作说明 + 结果
├── requirements.txt         # Python 依赖清单
├── data/                    # 9 张原始 CSV
├── docs/
│   ├── 数据字典.md           # 表字段、行数、重复主键检查
│   ├── 口径表.md             # 所有指标口径的唯一来源
│   └── 业务结论文档.md        # memo：发现 → 归因 → 建议 → 验证
├── sql/
│   ├── 00_建表导入.sql       # 建库 + 建 9 张表 + 导数据 + QC
│   ├── 01_大盘总览.sql       # 必做 SQL 1
│   ├── 02_GMV月度趋势与环比.sql
│   ├── 03_GMV拆解_州与支付方式.sql
│   ├── 04_品类Top10.sql
│   ├── 05_订单生命周期漏斗.sql
│   ├── 06_RFM分层.sql
│   ├── 07_Cohort留存.sql
│   ├── 08_配送延迟与差评.sql
│   └── 09_卖家集中度.sql     # 可选 SQL
├── analysis/                # Python 数据质量、交叉复核、专题、绘图、一键 SQL
└── results/                 # SQL/Python 输出的 CSV 与 PNG
```

---

## 5. 完整操作流程

> 以下命令在 Windows PowerShell 中执行。所有相对路径命令默认在仓库根目录
> `E:\03_Development\DataAnalyst\olist-project` 下运行。

### 5.1 启动环境

```powershell
# 1) 进入项目目录
cd E:\03_Development\DataAnalyst\olist-project

# 2) 检查 MySQL 服务（Status = Running 即可）
Get-Service MySQL

# 若服务未启动：
Start-Service MySQL

# 3) 激活 conda 分析环境
conda activate ds_project

# 4) 新环境首次使用时安装依赖（已安装可跳过）
python -m pip install -r requirements.txt
```

### 5.2 设置本次会话的数据库密码

```powershell
# 只写入当前 PowerShell 会话，不要提交到 Git
$env:MYSQL_PWD='你的MySQL密码'
```

后续 mysql 客户端与 Python 脚本都会自动使用该变量，无需重复输入密码。
不想设置环境变量时，mysql 命令可改用 `-p` 手动输入，但 import_qc / run_all_sql 仍需要 `MYSQL_PWD`。

### 5.3 校验 MySQL local_infile

```powershell
# 查看 local_infile 是否已开启（预期 ON）
& 'E:\03_Development\MySQL\mysql-8.0.46-winx64\bin\mysql.exe' -h 127.0.0.1 -P 3306 -u root -e "SHOW VARIABLES LIKE 'local_infile';"
```

如果显示 `OFF`：检查 `E:\03_Development\MySQL\my.ini` 中是否有 `local_infile=ON`，然后管理员 PowerShell 执行 `Restart-Service MySQL`。

### 5.4 建库、建表、导入数据（sql/00）

```powershell
# 00 会执行：CREATE DATABASE olist → DROP 重建 9 张表 → 从 data/ 导入 9 张 CSV → SELECT 行数 QC
# PowerShell 不支持 '<' 输入重定向，因此用 cmd 包装执行；文件在仓库根目录执行
cmd /c '""E:\03_Development\MySQL\mysql-8.0.46-winx64\bin\mysql.exe" --local-infile=1 --default-character-set=utf8mb4 -h 127.0.0.1 -P 3306 -u root < "sql\00_建表导入.sql""'
```

脚本注释与行为：

| 步骤 | 说明 |
|---|---|
| `SET NAMES utf8mb4` | 统一客户端字符集 |
| `CREATE DATABASE IF NOT EXISTS olist` | 建库，不存在才创建 |
| 9 张 `CREATE TABLE` | 建主键/索引，不建外键（分析用途） |
| 9 条 `LOAD DATA LOCAL INFILE` | 从仓库 `data/` 读 CSV；空字符串转 NULL；reviews/翻译表用 CRLF |
| 末尾 `UNION ALL` 查询 | 输出 9 张表行数，作为导入 QC |

成功时应输出（QC 结果）：

```text
orders                              99441
order_items                        112650
order_payments                     103886
order_reviews                       99224
customers                           99441
sellers                              3095
products                            32951
geolocation                       1000163
product_category_name_translation      71
```

### 5.5 导入逐行核对（import_qc）

```powershell
# 用 Pandas/PyMySQL 将 reviews CSV 与数据库逐字段对比，找出差异行
python analysis/import_qc.py
```

预期结果：

```text
reviews: csv=99224 db=99224
csv rows not found in db (count): 0
db rows not found in csv (count): 0
```

### 5.6 直接查询数据库（可选）

```powershell
# 查看库与表
& 'E:\03_Development\MySQL\mysql-8.0.46-winx64\bin\mysql.exe' -h 127.0.0.1 -P 3306 -u root -e "SHOW DATABASES; USE olist; SHOW TABLES;"

# 示例：查看 orders 行数
& 'E:\03_Development\MySQL\mysql-8.0.46-winx64\bin\mysql.exe' -h 127.0.0.1 -P 3306 -u root -e "USE olist; SELECT COUNT(*) AS orders_cnt FROM orders;"
```

### 5.7 一键重跑 SQL 01–09 并导出结果

```powershell
# run_all_sql.py 会按顺序执行 sql/01~09，并把每个 SELECT 结果写入 results/<脚本名>_qN.csv
python analysis/run_all_sql.py
```

只跑单个脚本：

```powershell
python analysis/run_sql_export.py sql/04_品类Top10.sql
```

各 SQL 对应关系：

| SQL | 业务问题 | 输出 CSV |
|---|---|---|
| 01 大盘总览 | GMV/订单/买家/AOV/状态分布 | `01_大盘总览_q1/q2/q3.csv` |
| 02 GMV 月度趋势 | 月度 GMV 与环比 | `02_GMV月度趋势与环比_q1.csv` |
| 03 州与支付方式拆解 | GMV 集中在哪些州/支付方式 | `03_GMV拆解_州与支付方式_q1/q2.csv` |
| 04 品类 Top10 | 头部品类贡献、评分洼地 | `04_品类Top10_q1.csv` |
| 05 订单生命周期漏斗 | 各状态订单数与转化率 | `05_订单生命周期漏斗_q1/q2.csv` |
| 06 RFM 分层 | 各层客户数与 GMV 贡献 | `06_RFM分层_q1/q2.csv` |
| 07 Cohort 留存 | 首购月客群后续留存 | `07_Cohort留存_q1/q2.csv` |
| 08 配送延迟与差评 | 延迟分桶的差评率/评分 | `08_配送延迟与差评_q1/q2.csv` |
| 09 卖家集中度（可选） | Top N 卖家 GMV 占比 | `09_卖家集中度_q1/q2.csv` |

### 5.8 Python 数据质量、交叉复核、专题分析

```powershell
# 01 数据质量：缺失率、重复率、异常值检查
python analysis/01_数据质量.py

# 02 关键指标复核：Pandas 独立重算 GMV/买家/复购/Cohort，并与 SQL 基线比对
python analysis/02_关键指标复核.py

# 03 专题分析：配送延迟 vs 差评率，含 95% Wilson CI
python analysis/03_专题分析.py
```

### 5.9 生成图表

```powershell
# 02 趋势图：GMV 月度柱状 + 环比折线（MoM 从 2017-02 开始）
python analysis/02_plot_trend.py

# 03 差评率图：延迟分桶柱状 + 95% CI
python analysis/03_plot_delay.py
```

本机若用 ds_project 激活环境，conda 激活钩子已自动设置 `MKL_THREADING_LAYER=TBB`；绘图脚本内部也做了兜底，可直接运行。

### 5.10 复现核对

```powershell
# 若 results 与仓库基线完全一致，工作区应为空；有差异说明结果漂移，需要排查
git status
git diff -- results
```

---

## 6. 关键结果基线

> 完整口径见 [口径表.md](口径表.md)；复核明细见 `results/analysis_02_复核结果.csv`。

| 指标 | 基线值 | SQL 结果文件 | Python 复核 |
|---|---:|---|---|
| 有效订单量 | 98,199 | results/01_大盘总览_q1.csv | 一致 |
| 有效买家数 | 94,983 | results/01_大盘总览_q1.csv | 一致 |
| GMV（items 口径） | R$15,735,527.03 | results/01_大盘总览_q1.csv | 一致 |
| GMV（payments 核对） | R$15,739,137.01 | results/01_大盘总览_q2.csv | — |
| 两口径差额 | R$3,609.98（0.02%） | results/01_大盘总览_q1/q2.csv | 口径表已解释 |
| 客单价 AOV | R$160.24 | results/01_大盘总览_q1.csv | 一致 |
| 复购客户 / 复购率 | 2,887 / 3.04% | results/06_RFM分层_q2.csv | 一致 |
| Cohort 第 1 月加权留存 | 0.45% | results/07_Cohort留存_q1.csv | 一致 |
| 送达订单 / 送达率 | 96,478 / 97.02% | results/01_大盘总览_q3.csv | — |
| 延迟率（可比较已送达单） | 6.77%（6,534 / 96,470） | results/08_配送延迟与差评_q2.csv | results/analysis_03_配送延迟差评率.csv |

---

## 7. 口径要点

| 指标 | 口径 |
|---|---|
| 统计范围 | 2016-09-04 ~ 2018-10-17；有效订单剔除 canceled/unavailable |
| GMV | Σ(price + freight_value)；用 payments 合计交叉核对 |
| 订单量/买家 | 有商品明细的有效订单 98,199；买家按 customer_unique_id 去重 94,983 |
| 复购率 | 全周期购买 ≥2 单客户 ÷ 有购买客户 |
| Cohort 留存 | 首购月为 cohort；第 n 月有任意有效订单即回访；第 0 月 = 100% |
| RFM | R≤197/339 天；M≤R$75.25/R$152.09；F=复购（≥2 单） |
| 漏斗 | 正向状态序列 created→…→delivered；canceled/unavailable 单列 |
| 差评 / 延迟 | score≤2；已送达且日期完整订单，每单一评 |

---

## 8. SQL 结果明细

### 8.1 大盘总览（01）

```text
order_cnt  buyer_cnt  gmv           aov
98199      94983      15735527.03   160.24
```

订单状态分布：

| order_status | order_cnt | pct |
|---|---:|---:|
| delivered | 96,478 | 97.02 |
| shipped | 1,107 | 1.11 |
| canceled | 625 | 0.63 |
| unavailable | 609 | 0.61 |
| invoiced | 314 | 0.32 |
| processing | 301 | 0.30 |
| created | 5 | 0.01 |
| approved | 2 | 0.00 |

### 8.2 GMV 月度趋势与环比（02）

- 峰值：2017-11，GMV R$1,172,191.68，环比 +53.28%（Black Friday）
- 次月回落：2017-12 GMV R$861,526.77，环比 -26.50%
- 2018-01 回升：GMV R$1,101,920.01，环比 +27.90%
- 环比口径说明：2016-12 样本过稀，2017-01 环比无业务意义，图表中 MoM 从 2017-02 开始

### 8.3 州与支付方式拆解（03）

买家所在州 Top5（GMV 口径）：

| state | order_cnt | gmv | gmv_share |
|---|---:|---:|---:|
| SP | 41,125 | R$5,878,132.06 | 37.36% |
| RJ | 12,697 | R$2,115,667.56 | 13.45% |
| MG | 11,496 | R$1,843,074.43 | 11.71% |
| RS | 5,415 | R$877,290.59 | 5.58% |
| PR | 4,982 | R$794,196.61 | 5.05% |

支付方式：

| payment_type | order_cnt | amount | amount_share |
|---|---:|---:|---:|
| credit_card | 75,618 | R$12,350,042.56 | 78.47% |
| boleto | 19,539 | R$2,826,802.30 | 17.96% |
| voucher | 3,745 | R$349,874.40 | 2.22% |
| debit_card | 1,515 | R$212,417.75 | 1.35% |

### 8.4 品类 Top10（04）

| category | order_cnt | gmv | aov | avg_score | gmv_share |
|---|---:|---:|---:|---:|---:|
| health_beauty | 8,800 | R$1,437,665.78 | R$163.37 | 4.19 | 9.14% |
| watches_gifts | 5,604 | R$1,298,292.47 | R$231.67 | 4.08 | 8.25% |
| bed_bath_table | 9,399 | R$1,240,386.13 | R$131.97 | 3.98 | 7.88% |
| sports_leisure | 7,673 | R$1,147,244.63 | R$149.52 | 4.18 | 7.29% |
| computers_accessories | 6,654 | R$1,050,941.58 | R$157.94 | 4.04 | 6.68% |
| furniture_decor | 6,425 | R$899,626.04 | R$140.02 | 4.03 | 5.72% |
| housewares | 5,847 | R$772,035.14 | R$132.04 | 4.16 | 4.91% |
| cool_stuff | 3,616 | R$704,086.24 | R$194.71 | 4.18 | 4.47% |
| auto | 3,872 | R$678,606.64 | R$175.26 | 4.11 | 4.31% |
| garden_tools | 3,505 | R$579,525.20 | R$165.34 | 4.15 | 3.68% |

### 8.5 订单生命周期漏斗（05）

| stage | order_cnt | step_pct | overall_pct |
|---|---:|---:|---:|
| created | 98,207 | — | 98.76% |
| approved | 98,202 | 99.99% | 98.75% |
| invoiced | 98,200 | 100.00% | 98.75% |
| processing | 97,886 | 99.68% | 98.44% |
| shipped | 97,585 | 99.69% | 98.13% |
| delivered | 96,478 | 98.87% | 97.02% |

终态流失单列：canceled 625、unavailable 609。

### 8.6 RFM 分层（06）

| segment | customer_cnt | gmv | customer_pct | gmv_pct |
|---|---:|---:|---:|---:|
| 高价值流失风险 | 20,922 | R$4,739,413.65 | 22.03% | 30.12% |
| 中期潜力 | 20,991 | R$4,540,301.76 | 22.10% | 28.85% |
| 近期高价值新客 | 20,385 | R$4,534,554.52 | 21.46% | 28.82% |
| 中期低额 | 10,806 | R$539,747.98 | 11.38% | 3.43% |
| 长期低价值沉默 | 10,695 | R$537,848.29 | 11.26% | 3.42% |
| 近期低额 | 10,179 | R$505,574.23 | 10.72% | 3.21% |
| 核心复购价值 | 1,005 | R$338,086.60 | 1.06% | 2.15% |

### 8.7 Cohort 留存（07）

- 23 个首购月 cohort，最大 cohort 7,188 人，最小 1 人，平均 4,129.7 人
- 完整留存矩阵 324 行，已补零到数据末日
- Cohort 第 1 月加权留存 0.45%，说明整体“买完即走”
- 完整矩阵见 `results/07_Cohort留存_q1.csv`

### 8.8 配送延迟与差评（08）

已送达且日期完整订单 96,470 单，延迟 6,534 单（6.77%）。

| bucket | delivered_cnt | reviewed_cnt | bad_cnt | bad_rate | avg_score | CI lower | CI upper |
|---|---:|---:|---:|---:|---:|---:|---:|
| 按时或提前 | 89,936 | 89,443 | 8,248 | 9.22% | 4.29 | 9.03% | 9.41% |
| 延迟1天 | 825 | 820 | 161 | 19.63% | 3.73 | 17.06% | 22.49% |
| 延迟2-3天 | 1,045 | 1,032 | 434 | 42.05% | 2.94 | 39.08% | 45.09% |
| 延迟4-7天 | 1,802 | 1,748 | 1,180 | 67.51% | 2.11 | 65.27% | 69.66% |
| 延迟8-14天 | 1,478 | 1,446 | 1,158 | 80.08% | 1.67 | 77.95% | 82.06% |
| 延迟15天以上 | 1,384 | 1,335 | 1,043 | 78.13% | 1.73 | 75.83% | 80.26% |

### 8.9 卖家集中度（09）

- 活跃卖家 3,053
- Top1 GMV 占比 1.58%
- Top5 合计 7.39%
- Top10 合计 12.86%
- Top20 合计 20.92%

卖家端高度分散，无单一大卖家依赖。

### 8.10 Python 交叉复核结果

```text
GMV(items)                15735527.03  diff=0.0    PASS
买家数(unique)                 94983  diff=0      PASS
复购客户(>=2单)                 2887  diff=0      PASS
复购率%                        3.04  diff=0      PASS
Cohort 第1月加权留存%          0.45  diff=0      PASS
```

---

## 9. 可视化

![GMV 月度趋势](../results/02_GMV月度趋势.png)

![配送延迟差评率](../results/analysis_03_配送延迟差评率.png)

---

## 10. 业务结论（memo 摘要）

1. **履约端整体健康，延迟是差评最强解释变量之一**：延迟 8–14 天订单差评率 80.08%，按时仅 9.22%。
2. **客户“买完即走”**：复购率仅 3.04%；“高价值流失风险”层 20,922 人贡献 30.12% GMV。
3. **需求端区域集中、供给端长尾**：SP 一州占 37.36%；Top20 卖家仅占 20.92%。
4. **头部品类存在“高销量低评分”洼地**：bed_bath_table 销量最高但平均分在 Top10 中最低（3.98）。
5. **大促脉冲显著**：2017-11 GMV 环比 +53.28%，次月回落 26.50%。

完整版见 [业务结论文档.md](业务结论文档.md)。

---

## 11. 局限与边界

- 巴西市场数据：方法可迁移，数值不直接照搬到中国市场。
- 结论为描述性相关/分层差异，不做因果推断。
- 评价正文缺失率高（标题 88%、正文 59%），但评分字段覆盖完整。
- 数据首尾月份样本稀疏（2017-01 前、2018-09 后），趋势结论以 2017-01 ~ 2018-08 为核心期。
- 发现 61 单送达早于审批的录入异常（0.06%），不影响主结论。

---

## 12. 常见问题

| 问题 | 处理 |
|---|---|
| MySQL 连不上 / 未知主机 | 用 `-h 127.0.0.1 -P 3306` 分开写参数 |
| local_infile=OFF | 确认 my.ini 配置后重启 MySQL 服务 |
| ds_project 绘图崩溃（0xc06d007f） | 设 `MKL_THREADING_LAYER=TBB` 后重新 `conda activate ds_project` |
| 新机器无法导入 data/ | 在仓库根目录执行 sql/00，LOAD DATA 使用相对路径 |
| 数字对不上 | 先看 docs/口径表.md，再重跑 run_all_sql 与 Python 复核 |
