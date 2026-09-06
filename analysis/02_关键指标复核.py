# 02_关键指标复核.py | 用 Pandas 独立重算关键指标，与 SQL 结果（results 基线）比对
import os
import pandas as pd

DATA = r"E:\03_Development\olist-data"
ROOT = r"E:\03_Development\DataAnalyst\olist-project"
OUT = os.path.join(ROOT, "results")

orders = pd.read_csv(os.path.join(DATA, "olist_orders_dataset.csv"), parse_dates=["order_purchase_timestamp"])
items = pd.read_csv(os.path.join(DATA, "olist_order_items_dataset.csv"))
customers = pd.read_csv(os.path.join(DATA, "olist_customers_dataset.csv"))

valid = orders["order_status"].isin(["created", "approved", "invoiced", "processing", "shipped", "delivered"])
m = orders[valid].merge(items, on="order_id", how="inner").merge(customers, on="customer_id", how="inner")

gmv = round(float(m["price"].sum() + m["freight_value"].sum()), 2)
buyers = m["customer_unique_id"].nunique()
freq = m.groupby("customer_unique_id")["order_id"].nunique()
repeat_customers = int((freq >= 2).sum())
repeat_rate = round(100 * repeat_customers / buyers, 2)

# Cohort 加权第 1 月留存（同 SQL7 口径：首购月=首单月，第 n 月有任意有效订单）
m = m.copy()
m["month"] = m["order_purchase_timestamp"].dt.to_period("M")
first = m.groupby("customer_unique_id")["month"].min().rename("cohort").reset_index()
active = m[["customer_unique_id", "month"]].drop_duplicates().rename(columns={"month": "act"})
joined = first.merge(active, on="customer_unique_id")
joined["mi"] = (joined["act"].dt.year - joined["cohort"].dt.year) * 12 + (joined["act"].dt.month - joined["cohort"].dt.month)
size = joined.groupby("cohort")["customer_unique_id"].nunique().rename("size")
m1 = joined[joined["mi"] == 1].groupby("cohort")["customer_unique_id"].nunique().rename("ret1")
ret = pd.concat([size, m1], axis=1).fillna(0)
w_m1 = round(100 * float(ret["ret1"].sum()) / float(ret["size"].sum()), 2)

# SQL 基线（来源：results/01_大盘总览_q1.csv；SQL6/7 已验证）
targets = [
    ("GMV(items)", gmv, 15735527.03, "SQL1"),
    ("买家数(unique)", buyers, 94983, "SQL1"),
    ("复购客户(>=2单)", repeat_customers, 2887, "SQL6"),
    ("复购率%", repeat_rate, 3.04, "SQL6"),
    ("Cohort 第1月加权留存%", w_m1, 0.45, "SQL7"),
]
out_rows = []
all_ok = True
for name, val, tgt, src in targets:
    diff = round(val - tgt, 4)
    ok = abs(diff) <= 0.02
    all_ok &= ok
    out_rows.append({"metric": name, "python": val, "sql": tgt, "diff": diff, "status": "PASS" if ok else "FAIL"})
    print(f"{name:28s} python={val:<14} sql={tgt:<14} diff={diff} {out_rows[-1]['status']}")
pd.DataFrame(out_rows).to_csv(os.path.join(OUT, "analysis_02_复核结果.csv"), index=False, encoding="utf-8-sig")
print("ALL PASS" if all_ok else "HAS FAIL")