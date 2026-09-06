# 03_专题分析.py | 配送延迟 vs 差评率（含 95% Wilson CI）
# 口径同 SQL8：已送达订单、每单一评(MAX)、差评=score<=2
import os
import pandas as pd
from statsmodels.stats.proportion import proportion_confint

DATA = r"E:\03_Development\olist-data"
ROOT = r"E:\03_Development\DataAnalyst\olist-project"
OUT = os.path.join(ROOT, "results")
ORDER = ["按时或提前", "延迟1天", "延迟2-3天", "延迟4-7天", "延迟8-14天", "延迟15天以上"]

orders = pd.read_csv(os.path.join(DATA, "olist_orders_dataset.csv"), parse_dates=["order_delivered_customer_date", "order_estimated_delivery_date"])
reviews = pd.read_csv(os.path.join(DATA, "olist_order_reviews_dataset.csv"))

d = orders[(orders["order_status"] == "delivered") &
           orders["order_delivered_customer_date"].notna() &
           orders["order_estimated_delivery_date"].notna()].copy()
d["delay_days"] = (d["order_delivered_customer_date"] - d["order_estimated_delivery_date"]).dt.days
rv = (reviews.dropna(subset=["review_score"])
      .sort_values("review_score")
      .groupby("order_id")["review_score"].max().rename("score"))
d = d.merge(rv, left_on="order_id", right_index=True, how="left")

def bucket(x):
    if x <= 0: return "按时或提前"
    if x == 1: return "延迟1天"
    if x <= 3: return "延迟2-3天"
    if x <= 7: return "延迟4-7天"
    if x <= 14: return "延迟8-14天"
    return "延迟15天以上"

d["bucket"] = d["delay_days"].map(bucket)

def agg(s):
    reviewed = int(s["score"].notna().sum())
    bad = int((s["score"] <= 2).sum())
    return pd.Series({
        "delivered_cnt": len(s),
        "reviewed_cnt": reviewed,
        "bad_cnt": bad,
        "avg_score": round(float(s["score"].mean()), 2),
    })

g = d.groupby("bucket", sort=False).apply(agg, include_groups=False).reset_index()
g["bucket"] = pd.Categorical(g["bucket"], categories=ORDER, ordered=True)
g = g.sort_values("bucket").reset_index(drop=True)
g["bad_rate_pct"] = round(100 * g["bad_cnt"] / g["reviewed_cnt"], 2)
ci = [proportion_confint(b, n, alpha=0.05, method="wilson") for b, n in zip(g["bad_cnt"], g["reviewed_cnt"])]
g["ci_low_pct"] = [round(100 * x[0], 2) for x in ci]
g["ci_high_pct"] = [round(100 * x[1], 2) for x in ci]
g.to_csv(os.path.join(OUT, "analysis_03_配送延迟差评率.csv"), index=False, encoding="utf-8-sig")

delayed = int((d["delay_days"] > 0).sum())
print(f"已送达可比较订单: {len(d)}；延迟: {delayed} ({round(100*delayed/len(d),2)}%)")
print(g.to_string(index=False))