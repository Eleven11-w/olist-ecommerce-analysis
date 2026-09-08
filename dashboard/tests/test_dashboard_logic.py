from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from dashboard_logic import (  # noqa: E402
    calculate_kpis,
    category_summary,
    cohort_matrix,
    load_data,
    state_summary,
)


def test_frozen_baseline():
    sales, cohort = load_data(PROJECT_ROOT / "data")
    kpis = calculate_kpis(sales)
    assert len(sales) == 99_002
    assert kpis["orders"] == 98_199
    assert kpis["buyers"] == 94_983
    assert round(kpis["gmv"], 2) == 15_735_527.03
    assert round(kpis["aov"], 2) == 160.24
    assert category_summary(sales).iloc[0]["category_en"] == "health_beauty"
    assert state_summary(sales).iloc[0]["customer_state"] == "SP"
    assert len(cohort) == 324
    assert cohort["cohort_month"].nunique() == 23
    assert cohort_matrix(cohort, 30).shape[0] == 21


def test_known_segments():
    sales, _ = load_data(PROJECT_ROOT / "data")
    health = calculate_kpis(sales[sales["category_en"] == "health_beauty"])
    sp = calculate_kpis(sales[sales["customer_state"] == "SP"])
    nov = calculate_kpis(sales[sales["order_ym"] == "2017-11"])
    assert round(health["gmv"], 2) == 1_437_665.78
    assert health["orders"] == 8_800
    assert round(sp["gmv"], 2) == 5_878_132.06
    assert sp["orders"] == 41_125
    assert round(nov["gmv"], 2) == 1_172_191.68
