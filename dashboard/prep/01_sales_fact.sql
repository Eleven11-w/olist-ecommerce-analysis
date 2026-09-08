-- Olist 经营看板事实表
-- 粒度：(order_id, category_en) 唯一，即订单 × 英文品类。
-- 统一口径：有效订单剔除 canceled/unavailable；GMV = price + freight_value。
-- 不关联支付表，避免一对多关系放大 GMV。

WITH valid_orders AS (
  SELECT order_id, customer_id, order_purchase_timestamp
  FROM orders
  WHERE order_status NOT IN ('canceled', 'unavailable')
),
order_score AS (
  SELECT order_id, MAX(review_score) AS review_score
  FROM order_reviews
  WHERE review_score IS NOT NULL
  GROUP BY order_id
)
SELECT
  o.order_id,
  DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m-01') AS order_month,
  DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS order_ym,
  SHA2(c.customer_unique_id, 256) AS buyer_key,
  c.customer_state,
  COALESCE(t.product_category_name_english,
           p.product_category_name,
           '(missing)') AS category_en,
  ROUND(SUM(i.price + i.freight_value), 2) AS gmv,
  s.review_score
FROM valid_orders o
JOIN order_items i ON i.order_id = o.order_id
JOIN customers c ON c.customer_id = o.customer_id
JOIN products p ON p.product_id = i.product_id
LEFT JOIN product_category_name_translation t
       ON t.product_category_name = p.product_category_name
LEFT JOIN order_score s ON s.order_id = o.order_id
GROUP BY
  o.order_id,
  DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m-01'),
  DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m'),
  SHA2(c.customer_unique_id, 256),
  c.customer_state,
  COALESCE(t.product_category_name_english,
           p.product_category_name,
           '(missing)'),
  s.review_score
ORDER BY order_month, o.order_id, category_en;
