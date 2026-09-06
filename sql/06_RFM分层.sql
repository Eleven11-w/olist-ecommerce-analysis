-- 06_RFM分层.sql | 项目 A：Olist 电商经营分析
-- 业务问题：按 RFM 给客户分层，各层多少人、贡献多少 GMV
-- 口径：
--   客户 = 有效订单中有商品明细的 customer_unique_id（94,983）
--   快照 = orders 最大下单时间 2018-10-17 17:30:18
--   R(近度) = 快照日-最近下单日(天)；F = 去重有效订单数；M = Σ(price+freight)
--   数值阈值（由 94,983 客户分布按约 33%/67% 分位取整，2026-09-06 核验；换数据需重算）：
--     R：r=3 近度<=197 天；r=2 198~339 天；r=1 >=340 天
--     M：m=1 金额<=75.25；m=2 75.26~152.09；m=3 >=152.10
--     F：业务口径 freq>=2 视为复购（96.96% 客户仅 1 单，NTILE 无区分度）
--   分层规则（按优先级，互斥，合计=94,983 客户/15,735,527.03 GMV）：
--     核心复购价值 = R=3 且 freq>=2 且 M>=2
--     近期高价值新客 = R=3 且 freq=1 且 M>=2
--     近期低额     = R=3 且 M=1
--     中期潜力     = R=2 且 M>=2
--     中期低额     = R=2 且 M=1
--     高价值流失风险 = R=1 且 M>=2
--     长期低价值沉默 = R=1 且 M=1
-- 输出 CSV：results/06_RFM分层_q1.csv（分层）、_q2.csv（阈值记录）

WITH customer_stats AS (
  SELECT c.customer_unique_id AS cust,
         COUNT(DISTINCT o.order_id) AS freq,
         ROUND(SUM(i.price + i.freight_value), 2) AS monetary,
         DATEDIFF((SELECT MAX(order_purchase_timestamp) FROM orders),
                  MAX(o.order_purchase_timestamp)) AS recency
  FROM orders o
  JOIN order_items i ON i.order_id = o.order_id
  JOIN customers c   ON c.customer_id = o.customer_id
  WHERE o.order_status NOT IN ('canceled', 'unavailable')
  GROUP BY c.customer_unique_id
),
scored AS (
  SELECT cust, freq, monetary,
         CASE WHEN recency <= 197 THEN 3
              WHEN recency <= 339 THEN 2
              ELSE 1 END AS r_score,
         CASE WHEN monetary <= 75.25 THEN 1
              WHEN monetary <= 152.09 THEN 2
              ELSE 3 END AS m_score
  FROM customer_stats
),
segmented AS (
  SELECT cust, freq, monetary,
         CASE
           WHEN r_score = 3 AND freq >= 2 AND m_score >= 2 THEN '核心复购价值'
           WHEN r_score = 3 AND freq = 1 AND m_score >= 2 THEN '近期高价值新客'
           WHEN r_score = 3 AND m_score = 1 THEN '近期低额'
           WHEN r_score = 2 AND m_score >= 2 THEN '中期潜力'
           WHEN r_score = 2 AND m_score = 1 THEN '中期低额'
           WHEN r_score = 1 AND m_score >= 2 THEN '高价值流失风险'
           ELSE '长期低价值沉默'
         END AS segment
  FROM scored
)
SELECT segment,
       COUNT(*) AS customer_cnt,
       ROUND(SUM(monetary), 2) AS gmv,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS customer_pct,
       ROUND(100 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 2) AS gmv_pct
FROM segmented
GROUP BY segment
ORDER BY gmv DESC;

-- ② 阈值记录（口径留档，便于面试/复现）
SELECT 'R_score3' AS item, 'recency <= 197 days' AS rule, '约33%分位' AS note
UNION ALL SELECT 'R_score2', 'recency 198-339 days', '约33%-67%分位'
UNION ALL SELECT 'R_score1', 'recency >= 340 days', '>67%分位'
UNION ALL SELECT 'M_score3', 'monetary >= 152.10', '约>67%分位'
UNION ALL SELECT 'M_score2', 'monetary 75.26-152.09', '约33%-67%分位'
UNION ALL SELECT 'M_score1', 'monetary <= 75.25', '约<=33%分位'
UNION ALL SELECT 'F_repeat', 'freq >= 2', '复购客户（共2,887人/3.04%）';