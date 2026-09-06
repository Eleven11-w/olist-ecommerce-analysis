-- 08_配送延迟与差评.sql | 项目 A：Olist 电商经营分析
-- 业务问题：配送延迟多久，差评率/平均评分会怎样变化？
-- 口径：
--   只统计已送达订单（order_status='delivered' 且实际/预估送达日齐全）
--   延迟天数 = DATEDIFF(实际送达日, 预估送达日)，正数=延迟
--   差评 = review_score <= 2（每订单取一条评分，MAX 去重防 review_id 重复）
--   差评率 = 差评订单 / 有评分订单；avg_score 同在有评分订单上算
-- 输出：按时/延迟分桶后的 订单数、有评分数、差评率、平均评分
-- 输出 CSV：results/08_配送延迟与差评_q1.csv、_q2.csv

WITH delivered AS (
  SELECT o.order_id,
         DATEDIFF(o.order_delivered_customer_date, o.order_estimated_delivery_date) AS delay_days,
         (SELECT MAX(r.review_score)
          FROM order_reviews r
          WHERE r.order_id = o.order_id AND r.review_score IS NOT NULL) AS score
  FROM orders o
  WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
    AND o.order_estimated_delivery_date IS NOT NULL
)
SELECT CASE
         WHEN delay_days <= 0 THEN '按时或提前'
         WHEN delay_days = 1 THEN '延迟1天'
         WHEN delay_days BETWEEN 2 AND 3 THEN '延迟2-3天'
         WHEN delay_days BETWEEN 4 AND 7 THEN '延迟4-7天'
         WHEN delay_days BETWEEN 8 AND 14 THEN '延迟8-14天'
         ELSE '延迟15天以上'
       END AS bucket,
       COUNT(*) AS delivered_cnt,
       SUM(score IS NOT NULL) AS reviewed_cnt,
       SUM(score <= 2) AS bad_cnt,
       ROUND(100 * SUM(score <= 2) / NULLIF(SUM(score IS NOT NULL), 0), 2) AS bad_rate_pct,
       ROUND(AVG(score), 2) AS avg_score
FROM delivered
GROUP BY CASE
         WHEN delay_days <= 0 THEN '按时或提前'
         WHEN delay_days = 1 THEN '延迟1天'
         WHEN delay_days BETWEEN 2 AND 3 THEN '延迟2-3天'
         WHEN delay_days BETWEEN 4 AND 7 THEN '延迟4-7天'
         WHEN delay_days BETWEEN 8 AND 14 THEN '延迟8-14天'
         ELSE '延迟15天以上'
       END
ORDER BY MIN(delay_days);

-- ② 总览：延迟订单占比
WITH delivered AS (
  SELECT DATEDIFF(o.order_delivered_customer_date, o.order_estimated_delivery_date) AS delay_days
  FROM orders o
  WHERE o.order_status = 'delivered'
    AND o.order_delivered_customer_date IS NOT NULL
    AND o.order_estimated_delivery_date IS NOT NULL
)
SELECT COUNT(*) AS delivered_cnt,
       SUM(delay_days > 0) AS delayed_cnt,
       ROUND(100 * SUM(delay_days > 0) / COUNT(*), 2) AS delayed_pct
FROM delivered;