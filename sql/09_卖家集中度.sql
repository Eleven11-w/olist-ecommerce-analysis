-- 09_卖家集中度.sql | 项目 A：Olist 电商经营分析（可选）
-- 业务问题：GMV 是否集中在少数卖家？头部/长尾结构如何？
-- 口径：有效订单（NOT IN canceled/unavailable）× items GMV，按 seller_id 聚合
--   卖家 GMV = Σ(price+freight)；占比分母 = 全部有效卖家 GMV 合计（= SQL1 GMV）
-- 输出：① Top20 卖家排名与累计占比；② 活跃卖家数与 Top1/5/10/20 占比汇总
-- 输出 CSV：results/09_卖家集中度_q1.csv、_q2.csv

-- ① Top20 卖家
WITH seller_gmv AS (
  SELECT i.seller_id,
         ROUND(SUM(i.price + i.freight_value), 2) AS gmv
  FROM orders o
  JOIN order_items i ON i.order_id = o.order_id
  WHERE o.order_status NOT IN ('canceled', 'unavailable')
  GROUP BY i.seller_id
)
SELECT seller_id, gmv,
       ROUND(100 * gmv / SUM(gmv) OVER (), 2)              AS gmv_share_pct,
       ROUND(100 * SUM(gmv) OVER (ORDER BY gmv DESC) / SUM(gmv) OVER (), 2) AS cumulative_share_pct
FROM seller_gmv
ORDER BY gmv DESC
LIMIT 20;

-- ② 汇总：活跃卖家数与头部占比
WITH seller_gmv AS (
  SELECT i.seller_id,
         SUM(i.price + i.freight_value) AS gmv
  FROM orders o
  JOIN order_items i ON i.order_id = o.order_id
  WHERE o.order_status NOT IN ('canceled', 'unavailable')
  GROUP BY i.seller_id
),
ranked AS (
  SELECT gmv, ROW_NUMBER() OVER (ORDER BY gmv DESC) AS rn
  FROM seller_gmv
)
SELECT COUNT(*) AS active_sellers,
       ROUND(100 * SUM(CASE WHEN rn <= 1 THEN gmv ELSE 0 END) / SUM(gmv), 2) AS top1_pct,
       ROUND(100 * SUM(CASE WHEN rn <= 5 THEN gmv ELSE 0 END) / SUM(gmv), 2) AS top5_pct,
       ROUND(100 * SUM(CASE WHEN rn <= 10 THEN gmv ELSE 0 END) / SUM(gmv), 2) AS top10_pct,
       ROUND(100 * SUM(CASE WHEN rn <= 20 THEN gmv ELSE 0 END) / SUM(gmv), 2) AS top20_pct
FROM ranked;