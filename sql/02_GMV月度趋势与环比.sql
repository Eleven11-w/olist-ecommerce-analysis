-- 02_GMV月度趋势与环比.sql | 项目 A：Olist 电商经营分析
-- 业务问题：GMV 按月是多少，环比变化如何，能否看出大促/低谷月
-- 口径（与 01 一致）：GMV = Σ(price + freight_value)，剔除 canceled/unavailable；
--   按下单时间所属月份聚合；用 min/max 下单月生成连续月历，无订单月记 0，
--   避免缺月时 LAG 对错月份。首月无环比为 NULL。
-- 输出：ym, gmv, gmv_prev, mom_pct
-- 输出 CSV：results/02_GMV月度趋势与环比_q1.csv

WITH RECURSIVE months AS (
  SELECT DATE_FORMAT(MIN(order_purchase_timestamp), '%Y-%m-01') AS month_start
  FROM orders
  UNION ALL
  SELECT DATE_ADD(month_start, INTERVAL 1 MONTH)
  FROM months
  WHERE month_start < (SELECT DATE_FORMAT(MAX(order_purchase_timestamp), '%Y-%m-01') FROM orders)
),
monthly_gmv AS (
  SELECT DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m-01') AS month_start,
         ROUND(SUM(i.price + i.freight_value), 2) AS gmv
  FROM orders o
  JOIN order_items i ON i.order_id = o.order_id
  WHERE o.order_status NOT IN ('canceled', 'unavailable')
  GROUP BY DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m-01')
),
trend AS (
  SELECT m.month_start,
         COALESCE(g.gmv, 0) AS gmv,
         LAG(COALESCE(g.gmv, 0), 1) OVER (ORDER BY m.month_start) AS gmv_prev
  FROM months m
  LEFT JOIN monthly_gmv g ON g.month_start = m.month_start
)
SELECT DATE_FORMAT(month_start, '%Y-%m') AS ym,
       gmv,
       gmv_prev,
       CASE
         WHEN gmv_prev IS NULL OR gmv_prev = 0 THEN NULL
         ELSE ROUND((gmv - gmv_prev) / gmv_prev * 100, 2)
       END AS mom_pct
FROM trend
ORDER BY month_start;