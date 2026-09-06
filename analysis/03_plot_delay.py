import os
os.environ.setdefault("MKL_THREADING_LAYER", "TBB")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_csv(os.path.join(root, "results", "analysis_03_配送延迟差评率.csv"))

short_labels = [
    "On time / early",
    "1 day late",
    "2-3 days late",
    "4-7 days late",
    "8-14 days late",
    "15+ days late",
]
colors = ["#4E79A7", "#6B9AC9", "#E8A75D", "#D9734E", "#C14B4B", "#8C1F28"]

x = np.arange(len(df))
rate = df["bad_rate_pct"].to_numpy()
err_low = (rate - df["ci_low_pct"].to_numpy()).tolist()
err_high = (df["ci_high_pct"].to_numpy() - rate).tolist()

fig, ax = plt.subplots(figsize=(12.5, 6.8))
fig.subplots_adjust(top=0.85, bottom=0.17, left=0.075, right=0.975)

ax.axvspan(2.5, len(df) - 0.5, color="#C0392B", alpha=0.045, zorder=0)
ax.bar(
    x,
    rate,
    width=0.68,
    color=colors,
    edgecolor="white",
    linewidth=1.2,
    zorder=3,
)
ax.errorbar(
    x,
    rate,
    yerr=[err_low, err_high],
    fmt="none",
    ecolor="#3A3A3A",
    elinewidth=1.4,
    capsize=5,
    zorder=4,
)

for i, v in enumerate(rate):
    ax.text(
        i,
        v + 3.2,
        f"{v:.1f}%",
        ha="center",
        fontsize=13.5,
        fontweight="bold",
        color="#222222",
        zorder=5,
    )

tick_labels = [
    f"{short_labels[i]}\n(n={int(df['reviewed_cnt'].iloc[i]):,})"
    for i in range(len(df))
]
ax.set_xticks(x)
ax.set_xticklabels(tick_labels, fontsize=10)
ax.set_ylabel("Bad-review rate (%)", fontsize=12)
ax.set_ylim(0, 96)
ax.yaxis.set_major_locator(plt.MultipleLocator(10))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.tick_params(axis="y", labelsize=10)
ax.grid(axis="y", color="#E7E7E7", linewidth=0.8, zorder=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#B8B8B8")
ax.spines["bottom"].set_color("#B8B8B8")

fig.suptitle(
    "Delivery Delay and Bad-Review Rate",
    fontsize=18,
    fontweight="bold",
    y=0.99,
)
fig.text(
    0.5,
    0.925,
    "Delivered orders with complete dates  |  reviewed orders only  |  bad review = score <= 2",
    ha="center",
    fontsize=10.5,
    color="#6B6B6B",
)
fig.text(
    0.5,
    0.035,
    "Error bars: 95% Wilson CI  |  shaded area: delay >= 4 days",
    ha="center",
    fontsize=9,
    color="#8A8A8A",
)

out = os.path.join(root, "results", "analysis_03_配送延迟差评率.png")
fig.savefig(out, dpi=150)
print("saved:", out)
