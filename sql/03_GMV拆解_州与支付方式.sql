-- 03_GMV拆解_州与支付方式.sql | 项目 A：Olist 电商经营分析
-- 业务问题：GMV 集中在哪些州？支付方式结构如何？
-- 口径：有效订单 = order_status NOT IN ('canceled','unavailable')
--   ① 州拆解：GMV = Σ(price+freight)，按买家所在州 customer_state 聚合
--   ② 支付拆解：金额 = payment_value 合计（与 01 的 payments 口径一致，R$15,739,137.01），
--      一个订单可能有多条支付记录，按行金额计
-- 输出检查：各州 GMV 合计 = 01 的 items GMV；各支付方式金额合计 = 01 的 payments GMV
-- 输出 CSV：results/03_GMV拆解_州与支付方式_q1.csv、_q2.csv

-- ① 按州拆解（含累计占比）
WITH valid_orders AS (
  SELECT order_id, customer_id
  FROM orders
  WHERE order_status NOT IN ('canceled', 'unavailable')
),
state_gmv AS (
  SELECT c.customer_state AS state,
         COUNT(DISTINCT o.order_id)            AS order_cnt,
         ROUND(SUM(i.price + i.freight_value), 2) AS gmv
  FROM valid_orders o
  JOIN order_items i ON i.order_id = o.order_id
  JOIN customers c   ON c.customer_id = o.customer_id
  GROUP BY c.customer_state
)
SELECT state, order_cnt, gmv,
       ROUND(100 * gmv / SUM(gmv) OVER (), 2)                          AS gmv_share_pct,
       ROUND(SUM(gmv) OVER (ORDER BY gmv DESC), 2)                     AS cumulative_gmv,
       ROUND(100 * SUM(gmv) OVER (ORDER BY gmv DESC) / SUM(gmv) OVER (), 2) AS cumulative_share_pct
FROM state_gmv
ORDER BY gmv DESC;

-- ② 按支付方式拆解（按支付金额计）
WITH valid_orders AS (
  SELECT order_id
  FROM orders
  WHERE order_status NOT IN ('canceled', 'unavailable')
)
SELECT p.payment_type,
       COUNT(DISTINCT p.order_id) AS order_cnt,
       COUNT(*)                   AS payment_row_cnt,
       ROUND(SUM(p.payment_value), 2) AS amount,
       ROUND(100 * SUM(p.payment_value) / SUM(SUM(p.payment_value)) OVER (), 2) AS amount_share_pct
FROM valid_orders o
JOIN order_payments p ON p.order_id = o.order_id
GROUP BY p.payment_type
ORDER BY amount DESC;