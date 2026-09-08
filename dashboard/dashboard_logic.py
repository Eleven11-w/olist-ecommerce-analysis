from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def load_data(data_dir: Path = DATA_DIR) -> tuple[pd.DataFrame, pd.DataFrame]:
    sales = pd.read_csv(data_dir / "sales_fact.csv", parse_dates=["order_month"])
    cohort = pd.read_csv(data_dir / "cohort_retention.csv")
    return sales, cohort


def filter_sales(
    sales: pd.DataFrame,
    months: list[str] | None = None,
    states: list[str] | None = None,
    categories: list[str] | None = None,
) -> pd.DataFrame:
    filtered = sales
    if months:
        filtered = filtered[filtered["order_ym"].isin(months)]
    if states:
        filtered = filtered[filtered["customer_state"].isin(states)]
    if categories:
        filtered = filtered[filtered["category_en"].isin(categories)]
    return filtered


def calculate_kpis(sales: pd.DataFrame) -> dict[str, float | int]:
    gmv = float(sales["gmv"].sum())
    orders = int(sales["order_id"].nunique())
    buyers = int(sales["buyer_key"].nunique())
    return {
        "gmv": gmv,
        "orders": orders,
        "buyers": buyers,
        "aov": gmv / orders if orders else 0.0,
    }


def monthly_summary(sales: pd.DataFrame) -> pd.DataFrame:
    return (
        sales.groupby(["order_month", "order_ym"], as_index=False)
        .agg(gmv=("gmv", "sum"), orders=("order_id", "nunique"))
        .sort_values("order_month")
    )


def category_summary(sales: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    return (
        sales.groupby("category_en", as_index=False)
        .agg(
            gmv=("gmv", "sum"),
            orders=("order_id", "nunique"),
            avg_score=("review_score", "mean"),
        )
        .sort_values("gmv", ascending=False)
        .head(top_n)
    )


def state_summary(sales: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    return (
        sales.groupby("customer_state", as_index=False)
        .agg(gmv=("gmv", "sum"), orders=("order_id", "nunique"))
        .sort_values("gmv", ascending=False)
        .head(top_n)
    )


def cohort_matrix(cohort: pd.DataFrame, minimum_size: int = 30) -> pd.DataFrame:
    eligible = cohort[cohort["cohort_size"] >= minimum_size]
    return eligible.pivot(
        index="cohort_month", columns="month_index", values="retention_pct"
    ).sort_index()
