# 交互式 BI 看板

本目录是 Olist 分析项目的交付层，读取经过冻结和 QC 的派生数据，提供 Streamlit + Plotly 交互看板。

```powershell
# 从仓库根目录启动
python -m streamlit run dashboard/app.py

# 重新生成派生数据并执行质量检查
python dashboard/prep/make_c_data.py --source csv
python dashboard/prep/qc_c_data.py

# 验证筛选和指标逻辑
python -m pytest dashboard/tests/test_dashboard_logic.py -q
```

数据文件：

- `data/sales_fact.csv`：订单 × 英文品类粒度，用于 KPI、趋势和 Top10。
- `data/cohort_retention.csv`：首购 cohort × 月序号，用于留存热力图。

事实表仅保存 SHA-256 `buyer_key`，不公开原始 `customer_unique_id`。
