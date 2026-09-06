-- 00_建表导入.sql  |  项目 A：Olist 电商经营分析
-- 用途：一次性完成 建库(olist) + 建 9 张表 + 导入原始 CSV
-- 前置：
--   1) 数据在 E:/03_Development/olist-data/
--   2) MySQL 服务已启动，并已执行过（重启 MySQL 后需重跑）：
--        SET GLOBAL local_infile = 1;
--   3) 客户端必须加 --local-infile=1
-- 可重复执行：脚本会 DROP 并重建 9 张表（不会删除数据库本身）
-- 口径说明：CSV 空字符串统一导入为 NULL（review_comment_title/message 等为空也存 NULL）

SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS olist
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE olist;

-- ============ 建表（分析用途：建主键/索引，不建外键） ============

DROP TABLE IF EXISTS order_reviews;
DROP TABLE IF EXISTS order_payments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS sellers;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS geolocation;
DROP TABLE IF EXISTS product_category_name_translation;

CREATE TABLE orders (
  order_id                        VARCHAR(32)  NOT NULL,
  customer_id                     VARCHAR(32)  NOT NULL,
  order_status                    VARCHAR(20)  NULL,
  order_purchase_timestamp        DATETIME     NULL,
  order_approved_at               DATETIME     NULL,
  order_delivered_carrier_date    DATETIME     NULL,
  order_delivered_customer_date   DATETIME     NULL,
  order_estimated_delivery_date   DATETIME     NULL,
  PRIMARY KEY (order_id),
  KEY idx_orders_customer_id (customer_id),
  KEY idx_orders_purchase_ts (order_purchase_timestamp),
  KEY idx_orders_status (order_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE order_items (
  order_id            VARCHAR(32)  NOT NULL,
  order_item_id       INT          NOT NULL,
  product_id          VARCHAR(32)  NULL,
  seller_id           VARCHAR(32)  NULL,
  shipping_limit_date DATETIME     NULL,
  price               DECIMAL(10,2) NULL,
  freight_value       DECIMAL(10,2) NULL,
  PRIMARY KEY (order_id, order_item_id),
  KEY idx_items_product_id (product_id),
  KEY idx_items_seller_id (seller_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE order_payments (
  order_id            VARCHAR(32)  NOT NULL,
  payment_sequential  INT          NOT NULL,
  payment_type        VARCHAR(20)  NULL,
  payment_installments INT         NULL,
  payment_value       DECIMAL(10,2) NULL,
  PRIMARY KEY (order_id, payment_sequential),
  KEY idx_payments_type (payment_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- review_id 经校验存在重复，故不设主键；加自增 id 作为行标识
CREATE TABLE order_reviews (
  id                      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  review_id               VARCHAR(32)     NOT NULL,
  order_id                VARCHAR(32)     NOT NULL,
  review_score            TINYINT         NULL,
  review_comment_title    VARCHAR(255)    NULL,
  review_comment_message  TEXT            NULL,
  review_creation_date    DATETIME        NULL,
  review_answer_timestamp DATETIME        NULL,
  PRIMARY KEY (id),
  KEY idx_reviews_review_id (review_id),
  KEY idx_reviews_order_id (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE customers (
  customer_id             VARCHAR(32)  NOT NULL,
  customer_unique_id      VARCHAR(32)  NOT NULL,
  customer_zip_code_prefix VARCHAR(8)  NULL,
  customer_city           VARCHAR(64)  NULL,
  customer_state          CHAR(2)      NULL,
  PRIMARY KEY (customer_id),
  KEY idx_customers_unique_id (customer_unique_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE sellers (
  seller_id               VARCHAR(32)  NOT NULL,
  seller_zip_code_prefix  VARCHAR(8)   NULL,
  seller_city             VARCHAR(64)  NULL,
  seller_state            CHAR(2)      NULL,
  PRIMARY KEY (seller_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE products (
  product_id               VARCHAR(32)  NOT NULL,
  product_category_name    VARCHAR(64)  NULL,
  product_name_lenght      INT          NULL,
  product_description_lenght INT        NULL,
  product_photos_qty       INT          NULL,
  product_weight_g         INT          NULL,
  product_length_cm        INT          NULL,
  product_height_cm        INT          NULL,
  product_width_cm         INT          NULL,
  PRIMARY KEY (product_id),
  KEY idx_products_category (product_category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE geolocation (
  geolocation_zip_code_prefix VARCHAR(8)  NOT NULL,
  geolocation_lat             DECIMAL(10,7) NULL,
  geolocation_lng             DECIMAL(10,7) NULL,
  geolocation_city            VARCHAR(64)   NULL,
  geolocation_state           CHAR(2)       NULL,
  KEY idx_geo_zip (geolocation_zip_code_prefix)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE product_category_name_translation (
  product_category_name        VARCHAR(64) NOT NULL,
  product_category_name_english VARCHAR(64) NULL,
  PRIMARY KEY (product_category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============ 导入（reviews、翻译表为 CRLF；其余为 LF） ============

LOAD DATA LOCAL INFILE 'E:/03_Development/olist-data/olist_orders_dataset.csv'
INTO TABLE orders
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(order_id, customer_id, order_status,
 @purchase, @approved, @carrier, @delivered_customer, @estimated)
SET order_purchase_timestamp      = NULLIF(@purchase, ''),
    order_approved_at             = NULLIF(@approved, ''),
    order_delivered_carrier_date  = NULLIF(@carrier, ''),
    order_delivered_customer_date = NULLIF(@delivered_customer, ''),
    order_estimated_delivery_date = NULLIF(@estimated, '');

LOAD DATA LOCAL INFILE 'E:/03_Development/olist-data/olist_order_items_dataset.csv'
INTO TABLE order_items
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(order_id, order_item_id, product_id, seller_id, @ship_limit, price, freight_value)
SET shipping_limit_date = NULLIF(@ship_limit, '');

LOAD DATA LOCAL INFILE 'E:/03_Development/olist-data/olist_order_payments_dataset.csv'
INTO TABLE order_payments
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(order_id, payment_sequential, payment_type, payment_installments, payment_value);

LOAD DATA LOCAL INFILE 'E:/03_Development/olist-data/olist_order_reviews_dataset.csv'
INTO TABLE order_reviews
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(review_id, order_id, @score, @title, @message, @created, @answered)
SET review_score          = NULLIF(@score, ''),
    review_comment_title  = NULLIF(@title, ''),
    review_comment_message = NULLIF(@message, ''),
    review_creation_date  = NULLIF(@created, ''),
    review_answer_timestamp = NULLIF(@answered, '');

LOAD DATA LOCAL INFILE 'E:/03_Development/olist-data/olist_customers_dataset.csv'
INTO TABLE customers
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state);

LOAD DATA LOCAL INFILE 'E:/03_Development/olist-data/olist_sellers_dataset.csv'
INTO TABLE sellers
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(seller_id, seller_zip_code_prefix, seller_city, seller_state);

LOAD DATA LOCAL INFILE 'E:/03_Development/olist-data/olist_products_dataset.csv'
INTO TABLE products
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(product_id, @pcat, @name_len, @desc_len, @photos, @weight, @length, @height, @width)
SET product_category_name       = NULLIF(@pcat, ''),
    product_name_lenght         = NULLIF(@name_len, ''),
    product_description_lenght  = NULLIF(@desc_len, ''),
    product_photos_qty          = NULLIF(@photos, ''),
    product_weight_g            = NULLIF(@weight, ''),
    product_length_cm           = NULLIF(@length, ''),
    product_height_cm           = NULLIF(@height, ''),
    product_width_cm            = NULLIF(@width, '');

LOAD DATA LOCAL INFILE 'E:/03_Development/olist-data/olist_geolocation_dataset.csv'
INTO TABLE geolocation
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(geolocation_zip_code_prefix, @lat, @lng, @city, geolocation_state)
SET geolocation_lat  = NULLIF(@lat, ''),
    geolocation_lng  = NULLIF(@lng, ''),
    geolocation_city = NULLIF(@city, '');

LOAD DATA LOCAL INFILE 'E:/03_Development/olist-data/product_category_name_translation.csv'
INTO TABLE product_category_name_translation
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(product_category_name, product_category_name_english);

-- ============ 导入后立即 QC：行数 ============
SELECT 'orders' AS tbl, COUNT(*) AS rows_cnt FROM orders
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL SELECT 'order_payments', COUNT(*) FROM order_payments
UNION ALL SELECT 'order_reviews', COUNT(*) FROM order_reviews
UNION ALL SELECT 'customers', COUNT(*) FROM customers
UNION ALL SELECT 'sellers', COUNT(*) FROM sellers
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'geolocation', COUNT(*) FROM geolocation
UNION ALL SELECT 'product_category_name_translation', COUNT(*) FROM product_category_name_translation;
