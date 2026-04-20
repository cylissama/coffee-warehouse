import os
from typing import Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

st.set_page_config(page_title="Coffee Market Intelligence Dashboard", layout="wide")

MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SIGNAL_COLORS = {
    "Buy Now": "#1B7F5B",
    "Watch": "#D4A017",
    "Wait": "#C7522A",
    "Insufficient Data": "#8A8F98",
}

METRIC_OPTIONS: Dict[str, str] = {
    "Coffee Futures Close": "coffee_close",
    "Coffee Daily Return": "coffee_daily_return",
    "Coffee 7-Day Moving Average": "coffee_7day_ma",
    "Coffee 30-Day Moving Average": "coffee_30day_ma",
    "Coffee 30-Day Volatility": "coffee_30day_volatility",
    "Buy Opportunity Score": "buy_opportunity_score",
    "Average Temperature": "avg_temp",
    "Precipitation": "precipitation",
    "CPI Index": "cpi_value",
    "Fed Funds Rate": "fedfunds_value",
    "Fertilizer Price Index": "fertilizer_price_index",
}

TEMPLATES = {
    "Custom": {
        "metric": "Coffee Futures Close",
        "compare": "None",
        "grain": "Daily",
        "chart": "Line",
    },
    "Coffee price trend over time": {
        "metric": "Coffee Futures Close",
        "compare": "None",
        "grain": "Monthly",
        "chart": "Line",
    },
    "Coffee vs CPI": {
        "metric": "Coffee Futures Close",
        "compare": "CPI Index",
        "grain": "Monthly",
        "chart": "Line",
    },
    "Coffee vs Fed Funds": {
        "metric": "Coffee Futures Close",
        "compare": "Fed Funds Rate",
        "grain": "Monthly",
        "chart": "Line",
    },
    "Coffee vs fertilizer prices": {
        "metric": "Coffee Futures Close",
        "compare": "Fertilizer Price Index",
        "grain": "Monthly",
        "chart": "Line",
    },
    "Buy opportunity score over time": {
        "metric": "Buy Opportunity Score",
        "compare": "None",
        "grain": "Weekly",
        "chart": "Line",
    },
    "Coffee volatility vs precipitation": {
        "metric": "Coffee 30-Day Volatility",
        "compare": "Precipitation",
        "grain": "Weekly",
        "chart": "Scatter",
    },
    "Coffee vs temperature": {
        "metric": "Coffee Futures Close",
        "compare": "Average Temperature",
        "grain": "Weekly",
        "chart": "Scatter",
    },
}

WAREHOUSE_QUERY = """
SELECT
    f.date_id,
    r.region_name,
    f.coffee_close,
    f.coffee_daily_return,
    f.coffee_7day_ma,
    f.coffee_30day_ma,
    f.coffee_30day_volatility,
    f.avg_temp,
    f.precipitation,
    f.cpi_value,
    f.fedfunds_value,
    f.fertilizer_price_index,
    f.buy_opportunity_score,
    f.buy_signal
FROM fact_market_features f
JOIN dim_region r
    ON f.region_id = r.region_id
ORDER BY f.date_id;
"""


def get_engine():
    return create_engine(
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )


@st.cache_data(show_spinner=False)
def load_warehouse_data() -> pd.DataFrame:
    df = pd.read_sql(WAREHOUSE_QUERY, get_engine())
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df


def apply_template(template_name: str) -> Dict[str, str]:
    return TEMPLATES.get(template_name, TEMPLATES["Custom"])


def filter_dataframe(df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    return df[
        (df["date_id"].dt.date >= start_date)
        & (df["date_id"].dt.date <= end_date)
    ].copy()


def aggregate_dataframe(
    df: pd.DataFrame,
    selected_metric_col: str,
    compare_metric_col: Optional[str],
    time_grain: str,
) -> pd.DataFrame:
    working_df = df.copy()

    if time_grain == "Weekly":
        working_df["period"] = working_df["date_id"].dt.to_period("W").apply(lambda r: r.start_time)
    elif time_grain == "Monthly":
        working_df["period"] = working_df["date_id"].dt.to_period("M").apply(lambda r: r.start_time)
    else:
        working_df["period"] = working_df["date_id"]

    agg_cols: List[str] = [selected_metric_col]
    if compare_metric_col:
        agg_cols.append(compare_metric_col)

    result_df = (
        working_df.groupby("period")[agg_cols]
        .mean(numeric_only=True)
        .reset_index()
        .sort_values("period")
    )
    return result_df


def render_chart(
    result_df: pd.DataFrame,
    chart_type: str,
    selected_metric_col: str,
    compare_metric_col: Optional[str],
):
    chart_df = result_df.set_index("period")

    if chart_type == "Line":
        cols = [selected_metric_col] + ([compare_metric_col] if compare_metric_col else [])
        st.line_chart(chart_df[cols])
    elif chart_type == "Bar":
        cols = [selected_metric_col] + ([compare_metric_col] if compare_metric_col else [])
        st.bar_chart(chart_df[cols])
    elif chart_type == "Area":
        cols = [selected_metric_col] + ([compare_metric_col] if compare_metric_col else [])
        st.area_chart(chart_df[cols])
    elif chart_type == "Scatter":
        if compare_metric_col:
            scatter_df = result_df[[selected_metric_col, compare_metric_col]].dropna()
            st.scatter_chart(scatter_df, x=selected_metric_col, y=compare_metric_col)
        else:
            st.warning("Scatter chart requires a comparison metric. Please choose a second metric.")
    elif chart_type == "Histogram":
        histogram_df = result_df[[selected_metric_col]].dropna()
        fig = px.histogram(
            histogram_df,
            x=selected_metric_col,
            nbins=min(24, max(8, len(histogram_df) // 3)),
            color_discrete_sequence=["#7C4A2D"],
            title=f"Distribution of {selected_metric_col.replace('_', ' ').title()}",
        )
        fig.update_layout(
            template="plotly_white",
            height=360,
            margin=dict(l=20, r=20, t=60, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Box":
        box_cols = [selected_metric_col] + ([compare_metric_col] if compare_metric_col else [])
        box_df = result_df[box_cols].melt(var_name="metric", value_name="value").dropna()
        fig = px.box(
            box_df,
            x="metric",
            y="value",
            color="metric",
            color_discrete_sequence=["#7C4A2D", "#2B6CB0"],
            title="Distribution Range",
            points="outliers",
        )
        fig.update_layout(
            template="plotly_white",
            height=360,
            margin=dict(l=20, r=20, t=60, b=20),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)


def render_visual_snapshot(filtered_df: pd.DataFrame):
    ordered_df = filtered_df.sort_values("date_id").reset_index(drop=True).copy()
    ordered_df["month_label"] = ordered_df["date_id"].dt.strftime("%b")
    ordered_df["year"] = ordered_df["date_id"].dt.year.astype(str)

    st.markdown("---")
    st.subheader("Market Snapshot")
    st.caption("A quick visual read of price momentum, model conviction, weather pressure, and seasonal patterns.")

    latest = ordered_df.iloc[-1]
    latest_score = float(latest["buy_opportunity_score"]) if pd.notna(latest["buy_opportunity_score"]) else 0.0

    col1, col2, col3 = st.columns([1.55, 1.0, 1.0])

    with col1:
        price_fig = go.Figure()
        price_fig.add_trace(
            go.Scatter(
                x=ordered_df["date_id"],
                y=ordered_df["coffee_close"],
                mode="lines",
                name="Coffee Close",
                line=dict(color="#7C4A2D", width=3),
                fill="tozeroy",
                fillcolor="rgba(124, 74, 45, 0.12)",
            )
        )
        price_fig.add_trace(
            go.Scatter(
                x=ordered_df["date_id"],
                y=ordered_df["coffee_7day_ma"],
                mode="lines",
                name="7-Day Average",
                line=dict(color="#2B6CB0", width=2, dash="dash"),
            )
        )
        price_fig.update_layout(
            title="Coffee Price Momentum",
            template="plotly_white",
            height=330,
            margin=dict(l=20, r=20, t=60, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(price_fig, use_container_width=True)

    with col2:
        gauge_fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=latest_score,
                number={"suffix": "/100"},
                title={"text": "Buy Score Gauge"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#4F7942"},
                    "steps": [
                        {"range": [0, 45], "color": "#F8D7CF"},
                        {"range": [45, 60], "color": "#F7E5B2"},
                        {"range": [60, 100], "color": "#D3E8DC"},
                    ],
                    "threshold": {
                        "line": {"color": "#1F2937", "width": 3},
                        "thickness": 0.75,
                        "value": latest_score,
                    },
                },
            )
        )
        gauge_fig.update_layout(
            template="plotly_white",
            height=330,
            margin=dict(l=20, r=20, t=60, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(gauge_fig, use_container_width=True)

    with col3:
        signal_counts = (
            ordered_df["buy_signal"]
            .fillna("Insufficient Data")
            .value_counts()
            .reindex(["Buy Now", "Watch", "Wait", "Insufficient Data"], fill_value=0)
            .reset_index()
        )
        signal_counts.columns = ["buy_signal", "count"]
        donut_fig = px.pie(
            signal_counts,
            names="buy_signal",
            values="count",
            hole=0.62,
            color="buy_signal",
            color_discrete_map=SIGNAL_COLORS,
            title="Signal Mix",
        )
        donut_fig.update_traces(textinfo="percent+label")
        donut_fig.update_layout(
            template="plotly_white",
            height=330,
            margin=dict(l=20, r=20, t=60, b=20),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(donut_fig, use_container_width=True)

    col4, col5, col6 = st.columns([1.1, 1.15, 1.0])

    with col4:
        climate_df = ordered_df.dropna(subset=["avg_temp", "precipitation", "buy_signal"]).copy()
        if not climate_df.empty:
            climate_fig = px.scatter(
                climate_df,
                x="avg_temp",
                y="precipitation",
                color="buy_signal",
                size=climate_df["buy_opportunity_score"].fillna(20).clip(lower=10),
                color_discrete_map=SIGNAL_COLORS,
                hover_data={"date_id": True, "coffee_close": ":.2f", "buy_opportunity_score": ":.1f"},
                title="Weather Pressure Map",
                labels={"avg_temp": "Temperature (°C)", "precipitation": "Precipitation (mm)"},
            )
            climate_fig.update_layout(
                template="plotly_white",
                height=340,
                margin=dict(l=20, r=20, t=60, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(climate_fig, use_container_width=True)

    with col5:
        heatmap_df = ordered_df.dropna(subset=["buy_opportunity_score"]).copy()
        if not heatmap_df.empty:
            month_score = (
                heatmap_df.groupby(["year", "month_label"])["buy_opportunity_score"]
                .mean()
                .reset_index()
            )
            month_score["month_label"] = pd.Categorical(month_score["month_label"], categories=MONTH_ORDER, ordered=True)
            month_score = month_score.sort_values(["year", "month_label"])
            pivot_df = month_score.pivot(index="year", columns="month_label", values="buy_opportunity_score").reindex(columns=MONTH_ORDER)

            heatmap_fig = go.Figure(
                data=go.Heatmap(
                    z=pivot_df.values,
                    x=pivot_df.columns,
                    y=pivot_df.index,
                    colorscale=[
                        [0.0, "#C7522A"],
                        [0.45, "#F4D06F"],
                        [1.0, "#1B7F5B"],
                    ],
                    colorbar=dict(title="Score"),
                    hovertemplate="Year %{y}<br>Month %{x}<br>Avg Score %{z:.1f}<extra></extra>",
                )
            )
            heatmap_fig.update_layout(
                title="Monthly Buy Score Heatmap",
                template="plotly_white",
                height=340,
                margin=dict(l=20, r=20, t=60, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(heatmap_fig, use_container_width=True)

    with col6:
        monthly_return = (
            ordered_df.assign(month_label=ordered_df["date_id"].dt.strftime("%b"))
            .groupby("month_label")["coffee_daily_return"]
            .mean()
            .reindex(MONTH_ORDER)
            .dropna()
            .mul(100)
        )
        if not monthly_return.empty:
            return_fig = go.Figure(
                go.Bar(
                    x=monthly_return.index,
                    y=monthly_return.values,
                    marker_color=["#1B7F5B" if val >= 0 else "#C7522A" for val in monthly_return.values],
                )
            )
            return_fig.update_layout(
                title="Average Daily Return by Month",
                template="plotly_white",
                height=340,
                margin=dict(l=20, r=20, t=60, b=20),
                yaxis_title="Return (%)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(return_fig, use_container_width=True)


def build_buy_opportunity_context(filtered_df: pd.DataFrame) -> str:
    ordered_df = filtered_df.sort_values("date_id").reset_index(drop=True)
    latest = ordered_df.iloc[-1]
    context_notes: List[str] = []

    if pd.notna(latest["coffee_30day_ma"]):
        if latest["coffee_close"] >= latest["coffee_30day_ma"]:
            context_notes.append("coffee is trading above its 30-day average, which supports upside momentum")
        else:
            context_notes.append("coffee is trading below its 30-day average, which softens the near-term signal")

    fertilizer_window = ordered_df["fertilizer_price_index"].dropna().tail(31)
    if len(fertilizer_window) >= 2 and fertilizer_window.iloc[0] != 0:
        fertilizer_change = (fertilizer_window.iloc[-1] / fertilizer_window.iloc[0]) - 1
        if fertilizer_change > 0.01:
            context_notes.append("fertilizer input costs have risen over the last month")
        elif fertilizer_change < -0.01:
            context_notes.append("fertilizer input costs have eased over the last month")

    precip_7day_avg = ordered_df["precipitation"].tail(7).mean()
    precip_30day_avg = ordered_df["precipitation"].tail(30).mean()
    if pd.notna(precip_7day_avg) and pd.notna(precip_30day_avg) and precip_30day_avg > 0:
        if precip_7day_avg < precip_30day_avg * 0.9:
            context_notes.append("recent rainfall is below the recent monthly average")
        elif precip_7day_avg > precip_30day_avg * 1.1:
            context_notes.append("recent rainfall is above the recent monthly average")

    volatility_median = ordered_df["coffee_30day_volatility"].median()
    if pd.notna(latest["coffee_30day_volatility"]) and pd.notna(volatility_median):
        if latest["coffee_30day_volatility"] > volatility_median:
            context_notes.append("price volatility remains elevated")
        else:
            context_notes.append("price volatility is relatively contained")

    if not context_notes:
        return "The score is based on recent coffee momentum, weather, fertilizer costs, inflation, and interest-rate conditions."

    return "Current drivers include " + "; ".join(context_notes[:3]) + "."


def render_buy_opportunity_score(filtered_df: pd.DataFrame):
    ordered_df = filtered_df.sort_values("date_id").reset_index(drop=True)
    latest = ordered_df.iloc[-1]
    latest_score = latest["buy_opportunity_score"]

    st.markdown("---")
    st.subheader("Buy Opportunity Score")
    st.caption(
        "Experimental logistic-regression model estimating the probability that coffee prices will be higher 7 days from now."
    )

    if pd.isna(latest_score):
        st.warning("Not enough history is available yet to calculate a stable buy-opportunity score for the latest date.")
        return

    score_history = ordered_df["buy_opportunity_score"].dropna()
    score_delta = None
    if len(score_history) >= 8:
        score_delta = latest_score - score_history.iloc[-8]

    col1, col2, col3 = st.columns([1.1, 1.0, 2.2])
    if score_delta is None:
        col1.metric("7-Day Buy Score", f"{latest_score:.1f}/100")
    else:
        col1.metric("7-Day Buy Score", f"{latest_score:.1f}/100", f"{score_delta:+.1f} vs 7 days ago")

    col2.metric(
        "Current Signal",
        latest["buy_signal"],
        help="Buy Now is 60 or higher, Watch is 45 to 59.99, and Wait is below 45.",
    )

    col3.markdown("**Interpretation**")
    col3.write(build_buy_opportunity_context(ordered_df))

    st.progress(min(max(float(latest_score) / 100.0, 0.0), 1.0))
    st.caption(
        "Higher scores suggest a greater chance that coffee prices will be higher within the next week, which can make buying now look more attractive."
    )


def render_kpis(filtered_df: pd.DataFrame):
    latest = filtered_df.iloc[-1]
    avg_temp_period = filtered_df["avg_temp"].mean()
    total_precip_period = filtered_df["precipitation"].sum()

    latest_coffee_cents = float(latest["coffee_close"])
    latest_coffee_dollars = latest_coffee_cents / 100.0
    latest_ma_cents = float(latest["coffee_7day_ma"])
    latest_ma_dollars = latest_ma_cents / 100.0
    latest_fertilizer_index = float(latest["fertilizer_price_index"])

    st.subheader("Key Metrics")
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

    col1.metric(
        "Coffee Futures Close",
        f"{latest_coffee_cents:.2f} cents/lb",
        help="End-of-day coffee futures closing price.",
    )
    col1.caption(f"≈ ${latest_coffee_dollars:.4f} per lb")

    col2.metric(
        "7-Day Avg Futures Price",
        f"{latest_ma_cents:.2f} cents/lb",
        help="Average of the last 7 daily coffee futures closing prices.",
    )
    col2.caption(f"≈ ${latest_ma_dollars:.4f} per lb")

    col3.metric(
        "Avg Temperature",
        f"{avg_temp_period:.2f} °C",
        help="Average daily temperature across the selected period.",
    )

    col4.metric(
        "Total Precipitation",
        f"{total_precip_period:.2f} mm",
        help="Total rainfall across the selected period.",
    )

    col5.metric(
        "Latest CPI Index",
        f"{latest['cpi_value']:.2f}",
        help="Consumer Price Index, an inflation index rather than a dollar amount.",
    )

    col6.metric(
        "Latest Fed Funds Rate",
        f"{latest['fedfunds_value']:.2f}%",
        help="Effective Federal Funds Rate from FRED.",
    )

    col7.metric(
        "Fertilizer Price Index",
        f"{latest_fertilizer_index:.2f}",
        help="FRED producer price index for fertilizer manufacturing, used here as an agricultural input-cost proxy.",
    )


def render_overview_charts(filtered_df: pd.DataFrame):
    st.markdown("---")
    st.subheader("Overview Trends")

    col1, col2 = st.columns(2)
    with col1:
        st.caption("Coffee futures closing price, quoted in cents per pound.")
        st.line_chart(filtered_df.set_index("date_id")[["coffee_close", "coffee_7day_ma"]])
    with col2:
        st.caption("Weather context for the selected region.")
        st.line_chart(filtered_df.set_index("date_id")[["avg_temp", "precipitation"]])

    st.caption("Macroeconomic and agricultural input-cost context.")
    st.line_chart(filtered_df.set_index("date_id")[["cpi_value", "fedfunds_value", "fertilizer_price_index"]])

    st.caption("Experimental 7-day buy-opportunity score.")
    st.line_chart(filtered_df.set_index("date_id")[["buy_opportunity_score"]])


def main():
    df = load_warehouse_data()

    if df.empty:
        st.error("No data found in fact_market_features.")
        st.stop()

    st.title("Coffee Market Intelligence Dashboard")
    st.markdown(
        """
        This dashboard lets users explore coffee futures, weather, macroeconomic signals,
        fertilizer input-cost pressure, and an experimental buy-opportunity model
        from the warehouse without writing SQL.

        Use the **Information** page in the sidebar for data-source details, metric definitions,
        and ETL explanation.
        """
    )

    st.markdown("---")
    st.subheader("Quick Analysis Templates")
    template_name = st.selectbox("Choose a common analysis question", list(TEMPLATES.keys()), index=0)
    defaults = apply_template(template_name)

    st.markdown("---")
    st.subheader("Explore the Warehouse")

    min_date = df["date_id"].min().date()
    max_date = df["date_id"].max().date()

    col1, col2, col3 = st.columns(3)
    start_date = col1.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
    end_date = col2.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)
    selected_metric = col3.selectbox(
        "Primary Metric",
        list(METRIC_OPTIONS.keys()),
        index=list(METRIC_OPTIONS.keys()).index(defaults["metric"]),
    )

    compare_options = ["None"] + list(METRIC_OPTIONS.keys())
    col4, col5, col6 = st.columns(3)
    compare_metric_name = col4.selectbox(
        "Compare Against",
        compare_options,
        index=compare_options.index(defaults["compare"]),
    )
    time_grain = col5.selectbox(
        "Time Grain",
        ["Daily", "Weekly", "Monthly"],
        index=["Daily", "Weekly", "Monthly"].index(defaults["grain"]),
    )

    chart_options = ["Line", "Bar", "Area", "Histogram", "Box"]
    if compare_metric_name != "None":
        chart_options.append("Scatter")
    chart_type = col6.selectbox(
        "Chart Type",
        chart_options,
        index=chart_options.index(defaults["chart"]) if defaults["chart"] in chart_options else 0,
    )

    if start_date > end_date:
        st.error("Start Date must be before or equal to End Date.")
        st.stop()

    filtered_df = filter_dataframe(df, start_date, end_date)
    if filtered_df.empty:
        st.warning("No data found for the selected date range.")
        st.stop()

    selected_metric_col = METRIC_OPTIONS[selected_metric]
    compare_metric_col = METRIC_OPTIONS.get(compare_metric_name) if compare_metric_name != "None" else None

    result_df = aggregate_dataframe(filtered_df, selected_metric_col, compare_metric_col, time_grain)

    st.info(
        f"This query analyzes {selected_metric.lower()}"
        + (f" against {compare_metric_name.lower()}" if compare_metric_name != "None" else "")
        + f" using {time_grain.lower()} aggregation for the selected date range."
    )

    render_buy_opportunity_score(filtered_df)
    render_kpis(filtered_df)
    render_visual_snapshot(filtered_df)

    st.markdown("---")
    st.subheader("Query Result")
    st.write(
        f"Showing **{selected_metric}**"
        + (f" compared with **{compare_metric_name}**" if compare_metric_col else "")
        + f" at **{time_grain.lower()}** granularity from **{start_date}** to **{end_date}**."
    )

    render_chart(result_df, chart_type, selected_metric_col, compare_metric_col)
    st.dataframe(result_df, width="stretch")

    csv_data = result_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Query Result as CSV",
        data=csv_data,
        file_name="coffee_market_query_result.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.subheader("Summary Statistics")
    summary_cols = [selected_metric_col] + ([compare_metric_col] if compare_metric_col else [])
    summary_df = result_df[summary_cols].describe().transpose()
    st.dataframe(summary_df, width="stretch")

    render_overview_charts(filtered_df)

    with st.expander("View Filtered Warehouse Rows"):
        st.dataframe(filtered_df, width="stretch")


if __name__ == "__main__":
    main()
