from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard_logic import (
    calculate_kpis,
    category_summary,
    cohort_matrix,
    filter_sales,
    load_data,
    monthly_summary,
    state_summary,
)


NAVY = "#17324D"
BLUE = "#2878B5"
TEAL = "#2A9D8F"
GRID = "#E8EDF3"
PLOT_CONFIG = {"displayModeBar": False, "responsive": True}


st.set_page_config(page_title="Olist 电商经营看板", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background: #F6F8FB; }
    .block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 3rem; }
    h1, h2, h3 { color: #17324D; letter-spacing: -0.02em; }
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E7ECF2;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 3px 12px rgba(23, 50, 77, 0.06);
    }
    div[data-testid="stMetricLabel"] { color: #667085; }
    div[data-testid="stMetricValue"] {
        color: #17324D;
        font-size: clamp(1.65rem, 1.85vw, 2rem);
        font-weight: 700;
        overflow: visible;
        white-space: nowrap;
    }
    div[data-testid="stMetricValue"] > div {
        overflow: visible;
        text-overflow: clip;
    }
    div[data-testid="stPlotlyChart"] {
        background: #FFFFFF;
        border: 1px solid #E7ECF2;
        border-radius: 14px;
        padding: 8px;
        box-shadow: 0 3px 12px rgba(23, 50, 77, 0.05);
    }
    div[data-testid="stAlert"] { border-radius: 12px; }
    [data-testid="stSidebar"] { background: #EDF3F7; }
    header[data-testid="stHeader"] { display: none; }
    [data-testid="stToolbar"], #MainMenu, footer { visibility: hidden; }
    .eyebrow {
        color: #2A9D8F;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.2rem;
    }
    .subtitle { color: #667085; font-size: 0.98rem; margin-top: -0.55rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def cached_data():
    return load_data()


def polish_figure(fig, *, height: int = 390, left_margin: int = 60):
    fig.update_layout(
        height=height,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Arial, Microsoft YaHei, sans-serif", color=NAVY, size=13),
        title=dict(font=dict(size=18, color=NAVY), x=0.02, xanchor="left"),
        margin=dict(l=left_margin, r=30, t=70, b=45),
        hoverlabel=dict(bgcolor="#FFFFFF", font_color=NAVY, bordercolor="#D7E0EA"),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False, linecolor=GRID)
    fig.update_yaxes(showgrid=False, zeroline=False, linecolor=GRID)
    return fig


sales, cohort = cached_data()

st.markdown('<div class="eyebrow">Olist · E-commerce Analytics</div>', unsafe_allow_html=True)
st.title("Olist 电商经营看板")
st.markdown(
    '<div class="subtitle">从经营规模、品类结构、地域集中度到客户复购，形成一套可筛选的业务诊断视图。</div>',
    unsafe_allow_html=True,
)

overview_tab, cohort_tab = st.tabs(["经营总览", "客户留存"])

with overview_tab:
    with st.sidebar:
        st.markdown("### 筛选条件")
        st.caption("未选择表示查看全部数据，Top10 会随筛选结果重新计算。")
        st.caption("这些筛选仅作用于“经营总览”，不影响 Cohort 留存。")
        months = st.multiselect("月份", sorted(sales["order_ym"].dropna().unique()), placeholder="全部月份")
        states = st.multiselect("州", sorted(sales["customer_state"].dropna().unique()), placeholder="全部州")
        categories = st.multiselect(
            "品类", sorted(sales["category_en"].dropna().unique()), placeholder="全部品类"
        )
        st.divider()
        st.caption("指标口径")
        st.caption("有效订单剔除 canceled 与 unavailable；GMV = 商品金额 + 运费。")

    filtered = filter_sales(sales, months, states, categories)
    kpis = calculate_kpis(filtered)

    st.markdown("### 核心经营指标")
    k1, k2, k3, k4 = st.columns([1.25, 1, 1, 1])
    k1.metric("GMV", f"R$ {kpis['gmv']:,.0f}")
    k2.metric("有效订单", f"{kpis['orders']:,}")
    k3.metric("成交客户", f"{kpis['buyers']:,}")
    k4.metric("客单价 AOV", f"R$ {kpis['aov']:,.2f}")

    if filtered.empty:
        st.warning("当前筛选组合没有数据，请减少筛选条件。")
    else:
        monthly = monthly_summary(filtered)
        monthly_display = monthly[monthly["order_ym"] != "2018-09"]
        if monthly_display.empty:
            st.info("2018-09 为不完整月份，当前筛选后没有可展示的完整月份趋势。")
        else:
            fig_monthly = px.line(
                monthly_display,
                x="order_month",
                y="gmv",
                markers=True,
                title="GMV 月度走势",
                labels={"order_month": "月份", "gmv": "GMV"},
                custom_data=["orders"],
            )
            fig_monthly.update_traces(
                line=dict(color=BLUE, width=3),
                marker=dict(size=7, color="#FFFFFF", line=dict(color=BLUE, width=2)),
                fill="tozeroy",
                fillcolor="rgba(40, 120, 181, 0.12)",
                hovertemplate="<b>%{x|%Y-%m}</b><br>GMV：R$ %{y:,.0f}<br>订单：%{customdata[0]:,}<extra></extra>",
            )
            peak = monthly_display.loc[monthly_display["gmv"].idxmax()]
            fig_monthly.add_annotation(
                x=peak["order_month"],
                y=peak["gmv"],
                text=f"峰值 R$ {peak['gmv'] / 1_000_000:.2f}M",
                showarrow=True,
                arrowhead=0,
                arrowcolor="#98A2B3",
                ax=0,
                ay=-42,
                bgcolor="#FFFFFF",
                bordercolor="#D7E0EA",
                borderpad=5,
                font=dict(size=12, color=NAVY),
            )
            polish_figure(fig_monthly, height=400)
            fig_monthly.update_layout(hovermode="x unified")
            fig_monthly.update_xaxes(tickformat="%Y-%m", dtick="M3")
            fig_monthly.update_yaxes(tickprefix="R$ ", tickformat="~s")
            st.plotly_chart(fig_monthly, width="stretch", config=PLOT_CONFIG)
            st.caption("注：2018-09 仅有 1 条记录，属于不完整月份，已从趋势图中剔除；其他指标仍按当前筛选口径计算。")

        left, right = st.columns(2, gap="large")
        categories_top = category_summary(filtered).sort_values("gmv")
        states_top = state_summary(filtered).sort_values("gmv")
        category_top3_share = categories_top.nlargest(3, "gmv")["gmv"].sum() / kpis["gmv"]
        state_top3_share = states_top.nlargest(3, "gmv")["gmv"].sum() / kpis["gmv"]
        categories_top = categories_top.assign(
            gmv_label=categories_top["gmv"].map(lambda value: f"R$ {value / 1_000_000:.2f}M")
        )
        states_top = states_top.assign(
            gmv_label=states_top["gmv"].map(lambda value: f"R$ {value / 1_000_000:.2f}M")
        )

        fig_category = px.bar(
            categories_top,
            x="gmv",
            y="category_en",
            orientation="h",
            title=f"品类 GMV Top10 <span style='font-size:12px;color:#667085'>· Top3 占 {category_top3_share:.1%}</span>",
            labels={"category_en": "", "gmv": "GMV"},
            custom_data=["orders", "avg_score"],
            text="gmv_label",
        )
        fig_category.update_traces(
            marker=dict(color=categories_top["gmv"], colorscale=[[0, "#B9D9EE"], [1, BLUE]], line_width=0),
            texttemplate="%{text}",
            textposition="outside",
            textfont=dict(size=11, color=NAVY),
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>GMV：R$ %{x:,.0f}<br>订单：%{customdata[0]:,}"
                "<br>平均评分：%{customdata[1]:.2f}<extra></extra>"
            ),
        )
        polish_figure(fig_category, height=500, left_margin=175)
        fig_category.update_xaxes(
            tickprefix="R$ ", tickformat="~s", range=[0, categories_top["gmv"].max() * 1.27]
        )
        left.plotly_chart(fig_category, width="stretch", config=PLOT_CONFIG)

        fig_state = px.bar(
            states_top,
            x="gmv",
            y="customer_state",
            orientation="h",
            title=f"州 GMV Top10 <span style='font-size:12px;color:#667085'>· Top3 占 {state_top3_share:.1%}</span>",
            labels={"customer_state": "", "gmv": "GMV"},
            custom_data=["orders"],
            text="gmv_label",
        )
        fig_state.update_traces(
            marker=dict(color=states_top["gmv"], colorscale=[[0, "#BFE4DE"], [1, TEAL]], line_width=0),
            texttemplate="%{text}",
            textposition="outside",
            textfont=dict(size=11, color=NAVY),
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>GMV：R$ %{x:,.0f}<br>订单：%{customdata[0]:,}<extra></extra>",
        )
        polish_figure(fig_state, height=500, left_margin=65)
        fig_state.update_xaxes(tickprefix="R$ ", tickformat="~s", range=[0, states_top["gmv"].max() * 1.25])
        right.plotly_chart(fig_state, width="stretch", config=PLOT_CONFIG)

        leading_category = categories_top.iloc[-1]
        leading_state = states_top.iloc[-1]
        category_share = leading_category["gmv"] / kpis["gmv"]
        state_share = leading_state["gmv"] / kpis["gmv"]
        st.info(
            f"当前筛选下，领先品类 **{leading_category['category_en']}** 贡献 {category_share:.1%} GMV；"
            f"领先州 **{leading_state['customer_state']}** 贡献 {state_share:.1%} GMV。"
        )

with cohort_tab:
    st.markdown("### 客户首购 Cohort 留存")
    st.caption("按客户首次购买月份分组，观察其在后续月份是否再次购买。")

    control, explanation = st.columns([1, 3])
    with control:
        minimum_size = st.slider("最小 Cohort 规模", 1, 500, 30, 1)
    with explanation:
        st.info("M0 是首购当月，固定为 100%；颜色重点区分 M1 之后的复购水平。")

    matrix = cohort_matrix(cohort, minimum_size)
    if matrix.empty:
        st.warning("当前最小规模下没有可展示的 Cohort。")
    else:
        color_values = matrix.copy()
        later_values = matrix.drop(columns=[0], errors="ignore")
        color_max = max(float(later_values.max().max()), 0.01)
        if 0 in color_values.columns:
            color_values[0] = color_max

        labels = matrix.map(
            lambda value: "" if value != value else ("100%" if value == 100 else f"{value:.2f}%")
        )
        fig_cohort = go.Figure(
            data=go.Heatmap(
                z=color_values.values,
                x=[f"M{int(column)}" for column in matrix.columns],
                y=matrix.index,
                text=labels.values,
                customdata=matrix.values,
                texttemplate="%{text}",
                textfont=dict(size=11),
                colorscale=[[0, "#F1F7F5"], [0.35, "#B9DDD3"], [0.7, "#5FAF99"], [1, "#176B5B"]],
                zmin=0,
                zmax=color_max,
                colorbar=dict(title="M1+ 留存率", ticksuffix="%", thickness=12, len=0.75),
                hovertemplate="首购月：%{y}<br>月份：%{x}<br>留存率：%{customdata:.2f}%<extra></extra>",
                xgap=2,
                ygap=2,
            )
        )
        polish_figure(fig_cohort, height=max(560, 29 * matrix.shape[0]), left_margin=80)
        fig_cohort.update_layout(title="各首购月份的后续复购表现", margin=dict(l=80, r=55, t=70, b=45))
        fig_cohort.update_xaxes(side="top", showgrid=False)
        fig_cohort.update_yaxes(autorange="reversed", showgrid=False)
        st.plotly_chart(fig_cohort, width="stretch", config=PLOT_CONFIG)

    month_one = cohort[cohort["month_index"] == 1]
    weighted_month_one = month_one["retained_customers"].sum() / month_one["cohort_size"].sum()
    st.info(
        f"全量 M1 加权留存率为 **{weighted_month_one:.2%}**。后期 Cohort 观察窗口更短，"
        "不能直接与早期 Cohort 比较完整生命周期。"
    )

st.caption("数据来源：Olist Brazilian E-commerce · 结果为描述性分析")
