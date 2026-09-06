-- 05_订单生命周期漏斗.sql | 项目 A：Olist 电商经营分析
-- 业务问题：订单在生命周期各环节还剩多少？哪一环流失最大？
-- 口径：正向状态序列 created→approved→invoiced→processing→shipped→delivered
--   每一层 = “已达到该状态或更后状态”的订单数（状态按严重级别累积）
--   各层流失 = 上一层订单数 - 本层订单数；step_pct = 本层/上一层
--   canceled/unavailable 是终态流失，不进入正向层级，单列展示
-- 输出检查：created 层 = 订单总量；delivered 层 = 96,478
-- 输出 CSV：results/05_订单生命周期漏斗_q1.csv

SELECT stage, order_cnt,
       LAG(order_cnt) OVER (ORDER BY seq) AS prev_cnt,
       ROUND(100 * order_cnt / LAG(order_cnt) OVER (ORDER BY seq), 2) AS step_pct,
       ROUND(100 * order_cnt / (SELECT COUNT(*) FROM orders), 2)      AS overall_pct
FROM (
  SELECT 1 AS seq, 'created' AS stage,
         COUNT(*) AS order_cnt
  FROM orders
  WHERE order_status IN ('created','approved','invoiced','processing','shipped','delivered')
  UNION ALL
  SELECT 2, 'approved', COUNT(*)
  FROM orders
  WHERE order_status IN ('approved','invoiced','processing','shipped','delivered')
  UNION ALL
  SELECT 3, 'invoiced', COUNT(*)
  FROM orders
  WHERE order_status IN ('invoiced','processing','shipped','delivered')
  UNION ALL
  SELECT 4, 'processing', COUNT(*)
  FROM orders
  WHERE order_status IN ('processing','shipped','delivered')
  UNION ALL
  SELECT 5, 'shipped', COUNT(*)
  FROM orders
  WHERE order_status IN ('shipped','delivered')
  UNION ALL
  SELECT 6, 'delivered', COUNT(*)
  FROM orders
  WHERE order_status = 'delivered'
) t;

-- 终态流失单列：canceled + unavailable
SELECT order_status, COUNT(*) AS order_cnt
FROM orders
WHERE order_status IN ('canceled', 'unavailable')
GROUP BY order_status;