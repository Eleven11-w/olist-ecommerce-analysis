-- 04_品类Top10.sql | 项目 A：Olist 电商经营分析
-- 业务问题：哪些品类贡献最大 GMV？是否存在“高销量低评分 / 低销量高评分”？
-- 口径：有效订单 = NOT IN ('canceled','unavailable')
--   GMV        = Σ(price+freight)（items 口径，按产品品类聚合）
--   订单量     = 该品类出现过的去重订单数
--   品类客单价 = 品类 GMV / 品类订单量（说明：一个订单含多品类时会在各自品类里各计一次）
--   平均评分   = 订单-品类粒度均值：先对 (订单,品类) 去重，再为该组合匹配一条订单评分
--                （同一订单同一品类的多件商品不重复计入；review_id 重复先按 order_id 取 MAX）
--   缺失品类   = 无 product_category_name 的行（原 CSV 空值，导入为 NULL），单独归为 missing
-- 输出：category, gmv, order_cnt, aov, avg_score, gmv_share_pct，Top10
-- 输出 CSV：results/04_品类Top10_q1.csv

WITH valid_orders AS (
  SELECT order_id
  FROM orders
  WHERE order_status NOT IN ('canceled', 'unavailable')
),
cat_gmv AS (
  SELECT COALESCE(pr.product_category_name, '(missing)') AS cat_raw,
         COUNT(DISTINCT o.order_id)                         AS order_cnt,
         ROUND(SUM(i.price + i.freight_value), 2)           AS gmv
  FROM valid_orders o
  JOIN order_items i ON i.order_id = o.order_id
  JOIN products pr   ON pr.product_id = i.product_id
  GROUP BY COALESCE(pr.product_category_name, '(missing)')
),
order_cat AS (
  SELECT DISTINCT o.order_id,
         COALESCE(pr.product_category_name, '(missing)') AS cat_raw
  FROM valid_orders o
  JOIN order_items i ON i.order_id = o.order_id
  JOIN products pr   ON pr.product_id = i.product_id
),
order_score AS (
  SELECT order_id, MAX(review_score) AS score
  FROM order_reviews
  WHERE review_score IS NOT NULL
  GROUP BY order_id
),
cat_review AS (
  SELECT oc.cat_raw,
         COUNT(DISTINCT oc.order_id) AS reviewed_order_cnt,
         ROUND(AVG(os.score), 2)     AS avg_score
  FROM order_cat oc
  JOIN order_score os ON os.order_id = oc.order_id
  GROUP BY oc.cat_raw
)
SELECT COALESCE(t.product_category_name_english, g.cat_raw) AS category,
       g.order_cnt,
       g.gmv,
       ROUND(g.gmv / g.order_cnt, 2)                       AS aov,
       r.avg_score,
       r.reviewed_order_cnt,
       ROUND(100 * g.gmv / SUM(g.gmv) OVER (), 2)          AS gmv_share_pct
FROM cat_gmv g
LEFT JOIN cat_review r ON r.cat_raw = g.cat_raw
LEFT JOIN product_category_name_translation t
       ON t.product_category_name = NULLIF(g.cat_raw, '(missing)')
ORDER BY g.gmv DESC
LIMIT 10;