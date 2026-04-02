import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Coffee Market Intelligence Dashboard", layout="wide")

pg_engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)

query = """
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

df = pd.read_sql(query, pg_engine)

if df.empty:
    st.error("No data found in fact_market_summary.")
    st.stop()

df["date_id"] = pd.to_datetime(df["date_id"])

latest = df.iloc[-1]
avg_temp_period = df["avg_temp"].mean()
total_precip_period = df["precipitation"].sum()

latest_coffee_cents = float(latest["coffee_close"])
latest_coffee_dollars = latest_coffee_cents / 100.0
latest_ma_cents = float(latest["coffee_7day_ma"])
latest_ma_dollars = latest_ma_cents / 100.0

st.title("Coffee Market Intelligence Dashboard")
st.markdown("""
This dashboard shows how **coffee futures prices** relate to weather conditions and broader macroeconomic indicators.

Use the **Information** page in the sidebar for data-source details, metric definitions, and ETL explanation.
""")

st.markdown("---")
st.subheader("Explore the Warehouse")

min_date = df["date_id"].min().date()
max_date = df["date_id"].max().date()

colf1, colf2, colf3 = st.columns(3)

start_date = colf1.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
end_date = colf2.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)

metric_options = {
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

selected_metric = colf3.selectbox("Primary Metric", list(metric_options.keys()))

filtered_df = df[
    (df["date_id"].dt.date >= start_date) &
    (df["date_id"].dt.date <= end_date)
].copy()

compare_metric_name = st.selectbox(
    "Compare Against",
    ["None"] + list(metric_options.keys()),
    index=0
)

time_grain = st.selectbox(
    "Time Grain",
    ["Daily", "Weekly", "Monthly"],
    index=0
)

selected_metric_col = metric_options[selected_metric]
compare_metric_col = metric_options.get(compare_metric_name) if compare_metric_name != "None" else None

if filtered_df.empty:
    st.warning("No data found for the selected date range.")
    st.stop()

working_df = filtered_df.copy()

if time_grain == "Weekly":
    working_df["period"] = working_df["date_id"].dt.to_period("W").apply(lambda r: r.start_time)
elif time_grain == "Monthly":
    working_df["period"] = working_df["date_id"].dt.to_period("M").apply(lambda r: r.start_time)
else:
    working_df["period"] = working_df["date_id"]

agg_cols = [selected_metric_col]
if compare_metric_col:
    agg_cols.append(compare_metric_col)

result_df = (
    working_df.groupby("period")[agg_cols]
    .mean(numeric_only=True)
    .reset_index()
    .sort_values("period")
)

st.markdown("---")
st.subheader("Query Result")

st.write(
    f"Showing **{selected_metric}**"
    + (f" compared with **{compare_metric_name}**" if compare_metric_col else "")
    + f" at **{time_grain.lower()}** granularity from **{start_date}** to **{end_date}**."
)

chart_df = result_df.set_index("period")

if compare_metric_col:
    st.line_chart(chart_df[[selected_metric_col, compare_metric_col]])
else:
    st.line_chart(chart_df[[selected_metric_col]])

st.dataframe(result_df, use_container_width=True)

st.markdown("---")
st.subheader("Summary Statistics")

summary_cols = [selected_metric_col]
if compare_metric_col:
    summary_cols.append(compare_metric_col)

summary_df = result_df[summary_cols].describe().transpose()
st.dataframe(summary_df, use_container_width=True)

st.subheader("Key Metrics")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Coffee Futures Close",
    f"{latest_coffee_cents:.2f} cents/lb",
    help="End-of-day coffee futures closing price."
)
col1.caption(f"Equivalent to about ${latest_coffee_dollars:.4f} per lb")

col2.metric(
    "7-Day Avg Futures Price",
    f"{latest_ma_cents:.2f} cents/lb",
    help="Average of the last 7 daily coffee futures closing prices."
)
col2.caption(f"Equivalent to about ${latest_ma_dollars:.4f} per lb")

col3.metric(
    "Avg Temperature",
    f"{avg_temp_period:.2f} °C",
    help="Average daily temperature across the displayed period."
)

col4.metric(
    "Total Precipitation",
    f"{total_precip_period:.2f} mm",
    help="Total rainfall across the displayed period."
)

col5.metric(
    "Latest CPI Index",
    f"{latest['cpi_value']:.2f}",
    help="Consumer Price Index, an inflation index rather than a dollar amount."
)

st.markdown("---")

st.subheader("Coffee Futures Price Over Time")
st.caption("Daily coffee futures closing price, quoted in cents per pound.")
st.line_chart(df.set_index("date_id")["coffee_close"])

st.subheader("7-Day Average Coffee Futures Price")
st.caption("7-day moving average of coffee futures closing price.")
st.line_chart(df.set_index("date_id")["coffee_7day_ma"])

st.subheader("Temperature Over Time")
st.caption("Daily average temperature in the selected weather region, measured in °C.")
st.line_chart(df.set_index("date_id")["avg_temp"])

st.subheader("Precipitation Over Time")
st.caption("Daily precipitation in the selected region, measured in millimeters.")
st.line_chart(df.set_index("date_id")["precipitation"])

st.subheader("CPI Index Over Time")
st.caption("Consumer Price Index over time. This is an inflation index, not a dollar amount.")
st.line_chart(df.set_index("date_id")["cpi_value"])

st.markdown("---")

st.subheader("Raw Warehouse Data")
st.dataframe(df, use_container_width=True)