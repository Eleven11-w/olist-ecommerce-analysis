-- 01_大盘总览.sql | 项目 A：Olist 电商经营分析
-- 业务问题：平台整体盘子有多大（GMV/订单/买家/客单价），订单走到各状态的分布如何
-- 口径（见 docs/口径表.md）：
--   GMV    = Σ(price + freight_value)，仅统计 order_status NOT IN ('canceled','unavailable')
--   订单量 = 纳入 GMV 口径的订单数（去重 order_id）
--   买家数 = 有效订单对应 customer_unique_id 去重数
--   客单价 = GMV / 订单量
--   状态分布 = 全部订单按 order_status 分组
-- 输出检查：状态分布合计 = 订单总量；GMV 与 order_payments 合计一致
-- 输出 CSV：results/01_大盘总览_q1.csv（总览）、_q2.csv（payments 核对）、_q3.csv（状态分布）

-- ① 总览指标：GMV、订单量、买家数、客单价
WITH valid_orders AS (
  SELECT order_id, customer_id
  FROM orders
  WHERE order_status NOT IN ('canceled', 'unavailable')
)
SELECT
  COUNT(DISTINCT o.order_id)                       AS order_cnt,
  COUNT(DISTINCT c.customer_unique_id)             AS buyer_cnt,
  ROUND(SUM(i.price + i.freight_value), 2)         AS gmv,
  ROUND(SUM(i.price + i.freight_value)
        / COUNT(DISTINCT o.order_id), 2)           AS aov
FROM valid_orders o
JOIN order_items i ON i.order_id = o.order_id
JOIN customers c   ON c.customer_id = o.customer_id;

-- ② GMV 交叉核对：用 order_payments 的 payment_value 合计重算一遍
WITH valid_orders AS (
  SELECT order_id
  FROM orders
  WHERE order_status NOT IN ('canceled', 'unavailable')
)
SELECT
  COUNT(DISTINCT p.order_id)  AS orders_with_payment,
  ROUND(SUM(p.payment_value), 2) AS gmv_from_payments
FROM valid_orders o
JOIN order_payments p ON p.order_id = o.order_id;

-- ③ 订单状态分布（全部订单；合计应等于 orders 总数 99,441）
SELECT
  order_status,
  COUNT(*)                        AS order_cnt,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM orders
GROUP BY order_status
ORDER BY order_cnt DESC;
