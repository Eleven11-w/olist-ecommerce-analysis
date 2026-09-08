"""核对 BI 派生数据是否严格复现仓库的冻结基线。"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SALES_COLUMNS = {
    "order_id",
    "order_month",
    "order_ym",
    "buyer_key",
    "customer_state",
    "category_en",
    "gmv",
    "review_score",
}
failures = 0
checks = 0


def check(name: str, actual: object, expected: object) -> None:
    global checks, failures
    checks += 1
    passed = actual == expected
    print(f"{'PASS' if passed else 'FAIL'} | {name} | actual={actual} | expected={expected}")
    if not passed:
        failures += 1


def main() -> int:
    sales_path = ROOT / "data" / "sales_fact.csv"
    cohort_path = ROOT / "data" / "cohort_retention.csv"
    if not sales_path.is_file() or not cohort_path.is_file():
        print("FAIL | 数据文件不存在，请先运行 prep/make_c_data.py")
        return 1

    sales = pd.read_csv(sales_path, dtype={"order_id": "string", "buyer_key": "string"})
    cohort = pd.read_csv(cohort_path)

    check("sales columns", set(sales.columns), EXPECTED_SALES_COLUMNS)
    check("sales rows", len(sales), 99_002)
    check("duplicate order-category", int(sales.duplicated(["order_id", "category_en"]).sum()), 0)
    check("missing order_id", int(sales["order_id"].isna().sum()), 0)
    check("missing buyer_key", int(sales["buyer_key"].isna().sum()), 0)
    hashes_valid = bool(sales["buyer_key"].map(lambda value: bool(re.fullmatch(r"[0-9a-f]{64}", value))).all())
    check("buyer_key SHA-256 format", hashes_valid, True)
    check("order count", int(sales["order_id"].nunique()), 98_199)
    check("buyer count", int(sales["buyer_key"].nunique()), 94_983)
    gmv = round(float(sales["gmv"].sum()), 2)
    check("GMV", gmv, 15_735_527.03)
    check("AOV", round(gmv / sales["order_id"].nunique(), 2), 160.24)

    nov = sales.loc[sales["order_ym"].eq("2017-11")]
    check("2017-11 GMV", round(float(nov["gmv"].sum()), 2), 1_172_191.68)
    health = sales.loc[sales["category_en"].eq("health_beauty")]
    check("health_beauty orders", int(health["order_id"].nunique()), 8_800)
    check("health_beauty GMV", round(float(health["gmv"].sum()), 2), 1_437_665.78)
    sp = sales.loc[sales["customer_state"].eq("SP")]
    check("SP orders", int(sp["order_id"].nunique()), 41_125)
    check("SP GMV", round(float(sp["gmv"].sum()), 2), 5_878_132.06)

    check("cohort rows", len(cohort), 324)
    check("cohort count", int(cohort["cohort_month"].nunique()), 23)
    small = cohort.loc[cohort["cohort_size"].lt(30), "cohort_month"].nunique()
    check("cohorts below 30", int(small), 2)
    check("max cohort size", int(cohort["cohort_size"].max()), 7_188)
    month_zero = cohort.loc[cohort["month_index"].eq(0), "retention_pct"]
    check("month 0 all 100%", bool(month_zero.eq(100).all()), True)

    print(f"SUMMARY | passed={checks - failures} | failed={failures} | total={checks}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
