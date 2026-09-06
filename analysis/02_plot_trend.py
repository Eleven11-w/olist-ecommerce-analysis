import os
os.environ.setdefault("MKL_THREADING_LAYER", "TBB")
import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_csv(os.path.join(root, "results", "02_GMV月度趋势与环比_q1.csv"))
df["ym"] = pd.to_datetime(df["ym"])
core = df[(df["ym"] >= "2017-01-01") & (df["ym"] <= "2018-08-01")].copy().reset_index(drop=True)
mom_line = core[core["ym"] >= "2017-02-01"].copy()

BAR = "#4E79A7"
PEAK = "#E15759"
MOM = "#E15759"

fig, ax1 = plt.subplots(figsize=(13.5, 6.3))
fig.subplots_adjust(top=0.86, bottom=0.14, left=0.075, right=0.90)

ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
ax1.spines["left"].set_color("#B8B8B8")
ax1.spines["bottom"].set_color("#B8B8B8")
ax1.tick_params(axis="y", labelsize=10)
ax1.grid(axis="y", color="#E7E7E7", linewidth=0.8, zorder=0)

peak_idx = core["gmv"].idxmax()
peak_date = core.loc[peak_idx, "ym"]
peak_dn = mdates.date2num(peak_date)
bar_colors = [PEAK if i == peak_idx else BAR for i in range(len(core))]

ax1.axvspan(peak_dn - 15, peak_dn + 15, color=PEAK, alpha=0.07, zorder=1)
ax1.bar(
    core["ym"],
    core["gmv"] / 1e6,
    width=22,
    color=bar_colors,
    edgecolor="white",
    linewidth=0.8,
    zorder=3,
    label="GMV (R$ million)",
)
ax1.set_ylim(0, 1.5)
ax1.set_ylabel("GMV (R$ million)", fontsize=12)
ax1.yaxis.set_major_locator(plt.MultipleLocator(0.25))
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.2f}"))

ax2 = ax1.twinx()
ax2.plot(
    mom_line["ym"],
    mom_line["mom_pct"],
    color=MOM,
    linewidth=2.2,
    marker="o",
    markersize=4.5,
    markerfacecolor="white",
    markeredgewidth=1.5,
    zorder=4,
    label="MoM change (%)",
)
ax2.axhline(0, color="#A9A9A9", linewidth=1.0, linestyle=":", zorder=2)
ax2.set_ylabel("MoM change (%)", fontsize=12)
ax2.tick_params(axis="y", labelsize=10)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_color("#B8B8B8")

ax1.annotate(
    "Peak R$1.17M\nMoM +53.3%",
    xy=(peak_date, core.loc[peak_idx, "gmv"] / 1e6),
    xytext=(0, 8),
    textcoords="offset points",
    ha="center",
    va="bottom",
    fontsize=10,
    fontweight="bold",
    color=PEAK,
)

ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
plt.setp(ax2.get_xticklabels(), rotation=35, ha="right", fontsize=9.5)

handles, labels = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(
    handles + h2,
    labels + l2,
    loc="upper left",
    frameon=False,
    fontsize=10,
)

fig.suptitle(
    "GMV Monthly Trend and MoM Change",
    fontsize=17,
    fontweight="bold",
    y=0.98,
)
fig.text(
    0.5,
    0.92,
    "Jan 2017 - Aug 2018  |  GMV = sum(price + freight), valid orders  |  MoM starts Feb 2017 (Dec 2016 too sparse)",
    ha="center",
    fontsize=10,
    color="#6B6B6B",
)

out = os.path.join(root, "results", "02_GMV月度趋势.png")
fig.savefig(out, dpi=150)
print("saved:", out)
