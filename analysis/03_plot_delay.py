import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import pandas as pd

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_csv(root + r"\results\analysis_03_配送延迟差评率.csv")
en = {"按时或提前": "On time / early", "延迟1天": "1 day late", "延迟2-3天": "2-3 days late",
      "延迟4-7天": "4-7 days late", "延迟8-14天": "8-14 days late", "延迟15天以上": "15+ days late"}
x = [en[v] for v in df["bucket"]]
y = df["bad_rate_pct"].tolist()
err_low = (y - df["ci_low_pct"]).tolist()
err_high = (df["ci_high_pct"] - y).tolist()

fig, ax = plt.subplots(figsize=(11, 5.5))
ax.bar(range(len(x)), y, color="#4C72B0", alpha=0.9, label="Bad-review rate (%)")
ax.errorbar(range(len(x)), y, yerr=[err_low, err_high], fmt="none", ecolor="black", capsize=5, label="95% CI")
for i, v in enumerate(y):
    ax.text(i, v + 2, f"{v:.1f}%", ha="center")
ax.set_xticks(range(len(x)))
ax.set_xticklabels(x, rotation=18, ha="right")
ax.set_ylabel("Bad-review rate (%)")
ax.set_title("Delivery Delay vs Bad-Review Rate (95% Wilson CI)")
ax.legend(loc="upper left")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
out = root + r"\results\analysis_03_配送延迟差评率.png"
fig.savefig(out, dpi=150)
print("saved:", out)