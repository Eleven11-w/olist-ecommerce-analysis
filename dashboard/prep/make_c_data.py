"""生成交互看板使用的两个派生数据文件。

从仓库根目录运行：
python dashboard/prep/make_c_data.py --source mysql
python dashboard/prep/make_c_data.py --source csv
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
from pathlib import Path

import pandas as pd
import pymysql


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROJECT_ROOT = ROOT.parent
SALES_COLUMNS = [
    "order_id",
    "order_month",
    "order_ym",
    "buyer_key",
    "customer_state",
    "category_en",
    "gmv",
    "review_score",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成 Olist BI 看板数据")
    parser.add_argument("--source", choices=("mysql", "csv"), default="mysql")
    parser.add_argument("--project-root", type=Path, default=DEFAULT_PROJECT_ROOT)
    return parser.parse_args()


def load_from_mysql() -> pd.DataFrame:
    password = os.environ.get("MYSQL_PWD")
    if not password:
        raise RuntimeError("mysql 模式要求当前会话设置 MYSQL_PWD")

    sql = (ROOT / "prep" / "01_sales_fact.sql").read_text(encoding="utf-8")
    connection = pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password=password,
        database="olist",
        charset="utf8mb4",
    )
    try:
        return pd.read_sql_query(sql, connection)
    finally:
        connection.close()


def require_files(data_dir: Path, names: list[str]) -> None:
    missing = [name for name in names if not (data_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"仓库缺少原始文件: {', '.join(missing)}")


def load_from_csv(project_root: Path) -> pd.DataFrame:
    data_dir = project_root / "data"
    names = [
        "olist_orders_dataset.csv",
        "olist_order_items_dataset.csv",
        "olist_customers_dataset.csv",
        "olist_products_dataset.csv",
        "product_category_name_translation.csv",
        "olist_order_reviews_dataset.csv",
    ]
    require_files(data_dir, names)

    orders = pd.read_csv(
        data_dir / names[0],
        usecols=["order_id", "customer_id", "order_status", "order_purchase_timestamp"],
    )
    items = pd.read_csv(
        data_dir / names[1],
        usecols=["order_id", "product_id", "price", "freight_value"],
    )
    customers = pd.read_csv(
        data_dir / names[2],
        usecols=["customer_id", "customer_unique_id", "customer_state"],
    )
    products = pd.read_csv(
        data_dir / names[3],
        usecols=["product_id", "product_category_name"],
    )
    translation = pd.read_csv(data_dir / names[4])
    reviews = pd.read_csv(
        data_dir / names[5], usecols=["order_id", "review_score"]
    )

    orders = orders.loc[~orders["order_status"].isin(["canceled", "unavailable"])]
    frame = (
        orders.merge(items, on="order_id", validate="one_to_many")
        .merge(customers, on="customer_id", validate="many_to_one")
        .merge(products, on="product_id", validate="many_to_one")
        .merge(translation, on="product_category_name", how="left", validate="many_to_one")
    )
    frame["category_en"] = (
        frame["product_category_name_english"]
        .fillna(frame["product_category_name"])
        .fillna("(missing)")
    )
    frame["gmv"] = frame["price"] + frame["freight_value"]
    frame["order_month"] = frame["order_purchase_timestamp"].str[:7] + "-01"
    frame["order_ym"] = frame["order_purchase_timestamp"].str[:7]
    frame["buyer_key"] = frame["customer_unique_id"].map(
        lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest()
    )

    scores = reviews.dropna(subset=["review_score"]).groupby(
        "order_id", as_index=False
    )["review_score"].max()
    group_columns = [
        "order_id",
        "order_month",
        "order_ym",
        "buyer_key",
        "customer_state",
        "category_en",
    ]
    sales = frame.groupby(group_columns, as_index=False, dropna=False)["gmv"].sum()
    sales["gmv"] = sales["gmv"].round(2)
    return sales.merge(scores, on="order_id", how="left", validate="many_to_one")


def write_outputs(sales: pd.DataFrame, project_root: Path) -> None:
    missing = [column for column in SALES_COLUMNS if column not in sales.columns]
    if missing:
        raise ValueError(f"事实表缺少字段: {', '.join(missing)}")

    data_dir = ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    sales = sales[SALES_COLUMNS].sort_values(
        ["order_month", "order_id", "category_en"], kind="stable"
    )
    sales.to_csv(data_dir / "sales_fact.csv", index=False, encoding="utf-8-sig")

    cohort_source = project_root / "results" / "07_Cohort留存_q1.csv"
    if not cohort_source.is_file():
        raise FileNotFoundError(f"仓库缺少冻结结果: {cohort_source}")
    shutil.copyfile(cohort_source, data_dir / "cohort_retention.csv")

    print(f"source_project_root={project_root.resolve()}")
    print(f"sales_fact rows={len(sales):,}")
    print("wrote data/sales_fact.csv")
    print("copied data/cohort_retention.csv")


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    print(f"source_mode={args.source}")
    sales = load_from_mysql() if args.source == "mysql" else load_from_csv(project_root)
    write_outputs(sales, project_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
