import os
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

st.set_page_config(page_title="Coffee Market Intelligence Dashboard", layout="wide")

METRIC_OPTIONS: Dict[str, str] = {
    "Coffee Futures Close": "coffee_close",
    "Coffee Daily Return": "coffee_daily_return",
    "Coffee 7-Day Moving Average": "coffee_7day_ma",
    "Coffee 30-Day Moving Average": "coffee_30day_ma",
    "Coffee 30-Day Volatility": "coffee_30day_volatility",
    "Average Temperature": "avg_temp",
    "Precipitation": "precipitation",
    "CPI Index": "cpi_value",
    "Fed Funds Rate": "fedfunds_value",
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
    f.fedfunds_value
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



def render_chart(result_df: pd.DataFrame, chart_type: str, selected_metric_col: str, compare_metric_col: Optional[str]):
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



def render_kpis(filtered_df: pd.DataFrame):
    latest = filtered_df.iloc[-1]
    avg_temp_period = filtered_df["avg_temp"].mean()
    total_precip_period = filtered_df["precipitation"].sum()

    latest_coffee_cents = float(latest["coffee_close"])
    latest_coffee_dollars = latest_coffee_cents / 100.0
    latest_ma_cents = float(latest["coffee_7day_ma"])
    latest_ma_dollars = latest_ma_cents / 100.0

    st.subheader("Key Metrics")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

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

    st.caption("Macroeconomic context.")
    st.line_chart(filtered_df.set_index("date_id")[["cpi_value", "fedfunds_value"]])



def main():
    df = load_warehouse_data()

    if df.empty:
        st.error("No data found in fact_market_features.")
        st.stop()

    st.title("Coffee Market Intelligence Dashboard")
    st.markdown(
        """
        This dashboard lets users explore coffee futures, weather, and macroeconomic signals
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

    chart_options = ["Line", "Bar", "Area"]
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

    render_kpis(filtered_df)

    st.markdown("---")
    st.subheader("Query Result")
    st.write(
        f"Showing **{selected_metric}**"
        + (f" compared with **{compare_metric_name}**" if compare_metric_col else "")
        + f" at **{time_grain.lower()}** granularity from **{start_date}** to **{end_date}**."
    )

    render_chart(result_df, chart_type, selected_metric_col, compare_metric_col)
    st.dataframe(result_df, use_container_width=True)

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
    st.dataframe(summary_df, use_container_width=True)

    render_overview_charts(filtered_df)

    with st.expander("View Filtered Warehouse Rows"):
        st.dataframe(filtered_df, use_container_width=True)


if __name__ == "__main__":
    main()
