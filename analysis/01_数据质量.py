# 01_数据质量.py | 基于原始 CSV 的数据质量检查（与数据库口径一致：CSV 空串≈DB NULL）
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "results")

FILES = [
    ("olist_orders_dataset.csv", "orders", ["order_id"]),
    ("olist_order_items_dataset.csv", "order_items", ["order_id", "order_item_id"]),
    ("olist_order_payments_dataset.csv", "order_payments", ["order_id", "payment_sequential"]),
    ("olist_order_reviews_dataset.csv", "order_reviews", ["review_id"]),
    ("olist_customers_dataset.csv", "customers", ["customer_id"]),
    ("olist_sellers_dataset.csv", "sellers", ["seller_id"]),
    ("olist_products_dataset.csv", "products", ["product_id"]),
    ("olist_geolocation_dataset.csv", "geolocation", None),
    ("product_category_name_translation.csv", "product_category_name_translation", ["product_category_name"]),
]

rows_sum = []
col_miss = []
for fname, tbl, keys in FILES:
    df = pd.read_csv(os.path.join(DATA, fname))
    dup_key = int(df[keys].duplicated().sum()) if keys else "na"
    rows_sum.append({
        "table": tbl, "csv_rows": len(df),
        "duplicate_key_rows": dup_key,
        "duplicate_full_rows": int(df.duplicated().sum()),
        "columns": df.shape[1],
    })
    for col in df.columns:
        miss = int(df[col].isna().sum())
        if miss > 0:
            col_miss.append({"table": tbl, "column": col, "missing": miss,
                             "missing_pct": round(100 * miss / len(df), 2)})

sum_df = pd.DataFrame(rows_sum)
miss_df = pd.DataFrame(col_miss)
sum_df.to_csv(os.path.join(OUT, "analysis_01_数据质量_表级.csv"), index=False, encoding="utf-8-sig")
miss_df.to_csv(os.path.join(OUT, "analysis_01_数据质量_缺失明细.csv"), index=False, encoding="utf-8-sig")

# --- 业务异常检查 ---
orders = pd.read_csv(os.path.join(DATA, "olist_orders_dataset.csv"), parse_dates=[
    "order_purchase_timestamp", "order_approved_at",
    "order_delivered_carrier_date", "order_delivered_customer_date",
    "order_estimated_delivery_date"])
items = pd.read_csv(os.path.join(DATA, "olist_order_items_dataset.csv"))
payments = pd.read_csv(os.path.join(DATA, "olist_order_payments_dataset.csv"))
reviews = pd.read_csv(os.path.join(DATA, "olist_order_reviews_dataset.csv"))
products = pd.read_csv(os.path.join(DATA, "olist_products_dataset.csv"))

anomalies = {
    "orders_total": len(orders),
    "approval_before_purchase": int((orders["order_approved_at"] < orders["order_purchase_timestamp"]).sum()),
    "delivered_before_approved": int((orders["order_delivered_customer_date"] < orders["order_approved_at"]).sum()),
    "estimated_before_purchase": int((orders["order_estimated_delivery_date"] < orders["order_purchase_timestamp"]).sum()),
    "purchase_range": f"{orders['order_purchase_timestamp'].min()} ~ {orders['order_purchase_timestamp'].max()}",
    "item_price_le_0": int((items["price"] <= 0).sum()),
    "item_freight_lt_0": int((items["freight_value"] < 0).sum()),
    "payment_value_lt_0": int((payments["payment_value"] < 0).sum()),
    "review_score_out_of_1_5": int((~reviews["review_score"].between(1, 5)).sum()),
    "product_negative_dim": int((products[["product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"]].lt(0).any(axis=1)).sum()),
}
anom_df = pd.DataFrame([{"check": k, "result": str(v)} for k, v in anomalies.items()])
anom_df.to_csv(os.path.join(OUT, "analysis_01_数据质量_异常检查.csv"), index=False, encoding="utf-8-sig")

print("== 01_数据质量 表级 ==")
print(sum_df.to_string(index=False))
print("== 01_数据质量 主要缺失（缺失率降序前12） ==")
if len(miss_df):
    print(miss_df.sort_values("missing_pct", ascending=False).head(12).to_string(index=False))
print("== 01_数据质量 异常检查 ==")
print(anom_df.to_string(index=False))