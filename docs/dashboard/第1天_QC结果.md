# 第 1 天数据生成与 QC 结果

> 执行日期：2026-09-07
> 执行入口：`python dashboard/prep/make_c_data.py --source csv`
> 项目目录：`E:\03_Development\DataAnalyst\olist-project`

## 结论

数据生成成功，20 项 QC 全部通过，进程退出码为 0。负向检查返回退出码 1，证明 QC 失败能够阻止后续流程。数据层验收完成，可以进入看板制作阶段。

## 产物

| 文件 | 行数 | 大小 | SHA-256 |
|---|---:|---:|---|
| `dashboard/data/sales_fact.csv` | 99,002 | 14,373,822 bytes | `E0AA5715CCA622FC627C5564089E23365110FE7A5E7F825E5ACF9D590A8C4B4A` |
| `dashboard/data/cohort_retention.csv` | 324 | 7,645 bytes | `6A4E71510EC9E7221DEA2FE66B125112B29B9E44440BE542DADDF19C0E18E93C` |

## 20 项检查

| 类别 | 检查结果 |
|---|---|
| 结构 | 8 个必需字段齐全；`(order_id, category_en)` 重复数为 0；关键 ID 无缺失 |
| 数据最小化 | 94,983 个 `buyer_key` 全部符合 64 位 SHA-256 格式 |
| 总览 | 99,002 行；98,199 个订单；94,983 个买家；GMV R$15,735,527.03；AOV R$160.24 |
| 月份 | 2017-11 GMV 为 R$1,172,191.68 |
| 品类 | health_beauty 为 8,800 单，GMV R$1,437,665.78 |
| 州 | SP 为 41,125 单，GMV R$5,878,132.06 |
| Cohort | 324 行、23 个 cohort、2 个规模小于 30、最大规模 7,188、第 0 月全部为 100% |

## 执行边界

本轮自动化会话没有 `MYSQL_PWD`，所以使用仓库内冻结的原始 CSV 生成数据。`--source mysql` 及 `dashboard/prep/01_sales_fact.sql` 已实现，但数据库连接路径没有在本轮声称实测。两条路径共用同一 QC；以后用 MySQL 重跑时仍须达到 20/20 PASS。
