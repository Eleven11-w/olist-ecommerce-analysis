import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

root = r"E:\03_Development\DataAnalyst\olist-project"
df = pd.read_csv(root + r"\results\02_GMV月度趋势与环比_q1.csv")
df["ym"] = pd.to_datetime(df["ym"])
core = df[(df["ym"] >= "2017-01-01") & (df["ym"] <= "2018-08-01")].copy()

fig, ax1 = plt.subplots(figsize=(13, 5.5))
ax1.bar(core["ym"], core["gmv"] / 1e6, width=22, color="#4C72B0", label="GMV (R$ million)")
ax1.set_ylabel("GMV (R$ million)")
ax1.set_title("Olist Monthly GMV Trend and MoM Change (Jan 2017 - Aug 2018)")
ax2 = ax1.twinx()
ax2.plot(core["ym"], core["mom_pct"], color="#C44E52", marker="o", ms=4, label="MoM %")
ax2.set_ylabel("MoM %")
peak = core.loc[core["gmv"].idxmax()]
ax1.annotate(f"Peak {peak['ym'].strftime('%Y-%m')}", xy=(peak["ym"], peak["gmv"] / 1e6),
             xytext=(0, 8), textcoords="offset points", ha="center")
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc="upper left")
ax1.grid(axis="y", alpha=0.3)
fig.autofmt_xdate()
fig.tight_layout()
out = root + r"\results\02_GMV月度趋势.png"
fig.savefig(out, dpi=150)
print("saved:", out)