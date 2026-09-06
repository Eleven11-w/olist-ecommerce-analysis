-- 07_Cohort留存.sql | 项目 A：Olist 电商经营分析
-- 业务问题：2016-09~2018 各“首购月”客群在后续每月还有多少人回购，留存如何衰减
-- 口径：
--   客户 = 有效订单中有商品明细的 customer_unique_id
--   cohort 月 = 该客户第一笔有效订单的下单月
--   第 n 月留存 = cohort 客户中在首购后第 n 个月仍有任意有效订单的人数 / cohort 人数
--   第 0 个月 = 100%（定义）
--   完整矩阵：每个 cohort 补零到全局数据末日对应的月序号；不补数据期之后的“未来月”
--   微小客群提示：cohort_size<30 的月份噪音大（2016-09 n=2、2016-12 n=1）
-- 输出：q1 完整留存矩阵；q2 cohort 规模统计
-- 输出 CSV：results/07_Cohort留存_q1.csv、_q2.csv

WITH RECURSIVE cust_first AS (
  SELECT c.customer_unique_id AS cust,
         DATE_FORMAT(MIN(o.order_purchase_timestamp), '%Y-%m-01') AS cohort_month
  FROM orders o
  JOIN order_items i ON i.order_id = o.order_id
  JOIN customers c   ON c.customer_id = o.customer_id
  WHERE o.order_status NOT IN ('canceled', 'unavailable')
  GROUP BY c.customer_unique_id
),
active_months AS (
  SELECT c.customer_unique_id AS cust,
         DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m-01') AS act_month
  FROM orders o
  JOIN order_items i ON i.order_id = o.order_id
  JOIN customers c   ON c.customer_id = o.customer_id
  WHERE o.order_status NOT IN ('canceled', 'unavailable')
  GROUP BY c.customer_unique_id, DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m-01')
),
cohort_list AS (
  SELECT cohort_month, COUNT(*) AS size
  FROM cust_first
  GROUP BY cohort_month
),
max_index AS (
  SELECT TIMESTAMPDIFF(MONTH,
           (SELECT DATE_FORMAT(MIN(order_purchase_timestamp), '%Y-%m-01') FROM orders),
           (SELECT DATE_FORMAT(MAX(order_purchase_timestamp), '%Y-%m-01') FROM orders)) AS n
),
nums AS (
  SELECT 0 AS n FROM max_index
  UNION ALL
  SELECT nums.n + 1 FROM nums JOIN max_index ON nums.n < max_index.n
),
retention AS (
  SELECT f.cohort_month, f.cust, a.act_month,
         TIMESTAMPDIFF(MONTH, f.cohort_month, a.act_month) AS month_index
  FROM cust_first f
  JOIN active_months a ON a.cust = f.cust
)
SELECT DATE_FORMAT(cl.cohort_month, '%Y-%m') AS cohort_month,
       cl.size AS cohort_size,
       nums.n AS month_index,
       COALESCE(rc.retained_customers, 0) AS retained_customers,
       ROUND(100 * COALESCE(rc.retained_customers, 0) / cl.size, 2) AS retention_pct
FROM cohort_list cl
CROSS JOIN nums
LEFT JOIN (
  SELECT cohort_month, month_index, COUNT(DISTINCT cust) AS retained_customers
  FROM retention
  GROUP BY cohort_month, month_index
) rc ON rc.cohort_month = cl.cohort_month AND rc.month_index = nums.n
WHERE nums.n <= TIMESTAMPDIFF(MONTH, cl.cohort_month,
        (SELECT DATE_FORMAT(MAX(order_purchase_timestamp), '%Y-%m-01') FROM orders))
ORDER BY cl.cohort_month, nums.n;

-- ② cohort 规模统计（微小客群标注用）
WITH cust_first AS (
  SELECT c.customer_unique_id AS cust,
         DATE_FORMAT(MIN(o.order_purchase_timestamp), '%Y-%m-01') AS cohort_month
  FROM orders o
  JOIN order_items i ON i.order_id = o.order_id
  JOIN customers c   ON c.customer_id = o.customer_id
  WHERE o.order_status NOT IN ('canceled', 'unavailable')
  GROUP BY c.customer_unique_id
),
cohort_list AS (
  SELECT cohort_month, COUNT(*) AS size
  FROM cust_first
  GROUP BY cohort_month
)
SELECT COUNT(DISTINCT cohort_month) AS cohort_cnt,
       MIN(size) AS min_size,
       MAX(size) AS max_size,
       SUM(size < 30) AS small_cohort_cnt,
       ROUND(AVG(size), 1) AS avg_size
FROM cohort_list;