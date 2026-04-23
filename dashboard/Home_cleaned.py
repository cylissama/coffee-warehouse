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
PALETTE = {
    "ink": "#2F241F",
    "espresso": "#5B3A29",
    "mocha": "#8A5A3B",
    "oat": "#F6F0E8",
    "cream": "#FBF7F2",
    "mist": "#DDD1C3",
    "stone": "#8C7E73",
    "sage": "#6F8A6D",
    "olive": "#4E6A4D",
    "terracotta": "#C56C4B",
    "amber": "#D8A24A",
    "clay": "#A35D2D",
    "rose": "#F2DDD4",
    "butter": "#F8EBC2",
    "moss": "#D9E8D3",
}
SIGNAL_COLORS = {
    "Buy Now": PALETTE["olive"],
    "Watch": PALETTE["amber"],
    "Wait": PALETTE["terracotta"],
    "Insufficient Data": PALETTE["stone"],
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
    "BRL/USD Exchange Rate": "brl_usd_exchange_rate",
    "Milk Price Index": "milk_price_index",
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
    "Coffee vs BRL/USD": {
        "metric": "Coffee Futures Close",
        "compare": "BRL/USD Exchange Rate",
        "grain": "Monthly",
        "chart": "Line",
    },
    "Coffee vs milk inputs": {
        "metric": "Coffee Futures Close",
        "compare": "Milk Price Index",
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
    f.brl_usd_exchange_rate,
    f.milk_price_index,
    f.buy_opportunity_score,
    f.buy_signal
FROM fact_market_features f
JOIN dim_region r
    ON f.region_id = r.region_id
ORDER BY f.date_id;
"""


def inject_theme():
    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600;700&family=Manrope:wght@400;500;600;700&display=swap');

            :root {{
                --ink: {PALETTE["ink"]};
                --espresso: {PALETTE["espresso"]};
                --mocha: {PALETTE["mocha"]};
                --oat: {PALETTE["oat"]};
                --cream: {PALETTE["cream"]};
                --mist: {PALETTE["mist"]};
                --stone: {PALETTE["stone"]};
                --sage: {PALETTE["sage"]};
                --olive: {PALETTE["olive"]};
                --terracotta: {PALETTE["terracotta"]};
                --amber: {PALETTE["amber"]};
                --clay: {PALETTE["clay"]};
            }}

            .stApp {{
                background:
                    radial-gradient(circle at top left, rgba(216, 162, 74, 0.18), transparent 28%),
                    radial-gradient(circle at top right, rgba(111, 138, 109, 0.16), transparent 24%),
                    linear-gradient(180deg, #fcf8f3 0%, #f6efe6 42%, #f9f4ee 100%);
                color: var(--ink);
                font-family: 'Manrope', sans-serif;
            }}

            .stApp [data-testid="stAppViewContainer"] {{
                background: transparent;
            }}

            .stApp [data-testid="stHeader"] {{
                background: rgba(251, 247, 242, 0.72);
                backdrop-filter: blur(10px);
            }}

            .stApp [data-testid="stToolbar"] {{
                right: 1rem;
            }}

            .block-container {{
                max-width: 1450px;
                padding-top: 4.6rem;
                padding-bottom: 3rem;
            }}

            h1, h2, h3 {{
                font-family: 'Fraunces', serif;
                color: var(--espresso);
                letter-spacing: -0.02em;
            }}

            h1 {{
                font-size: 3rem;
                margin-bottom: 0.2rem;
            }}

            h2 {{
                font-size: 1.7rem;
                margin-top: 0.6rem;
            }}

            p, label, [data-testid="stCaptionContainer"], .stMarkdown, .stText {{
                color: var(--ink);
                font-family: 'Manrope', sans-serif;
            }}

            [data-testid="stMetric"] {{
                background: rgba(251, 247, 242, 0.82);
                border: 1px solid rgba(139, 90, 59, 0.12);
                border-radius: 20px;
                padding: 1rem 1rem 0.8rem 1rem;
                box-shadow: 0 14px 30px rgba(91, 58, 41, 0.08);
            }}

            [data-testid="stMetricLabel"] {{
                color: var(--stone);
                font-weight: 700;
                letter-spacing: 0.02em;
                text-transform: uppercase;
                font-size: 0.75rem;
            }}

            [data-testid="stMetricValue"] {{
                color: var(--espresso);
                font-family: 'Fraunces', serif;
            }}

            .stAlert {{
                border-radius: 18px;
                border: 1px solid rgba(139, 90, 59, 0.12);
            }}

            .stDownloadButton button, .stButton button {{
                background: linear-gradient(135deg, var(--espresso), var(--mocha));
                color: white;
                border: none;
                border-radius: 999px;
                font-weight: 700;
                padding: 0.6rem 1.1rem;
                box-shadow: 0 10px 22px rgba(91, 58, 41, 0.18);
            }}

            .stDownloadButton button:hover, .stButton button:hover {{
                background: linear-gradient(135deg, var(--clay), var(--espresso));
                color: white;
            }}

            div[data-baseweb="select"] > div,
            .stDateInput > div > div,
            .stNumberInput > div > div,
            .stTextInput > div > div {{
                background: rgba(251, 247, 242, 0.9);
                border-radius: 16px;
                border: 1px solid rgba(139, 90, 59, 0.14);
            }}

            .stExpander {{
                background: rgba(251, 247, 242, 0.72);
                border: 1px solid rgba(139, 90, 59, 0.12);
                border-radius: 18px;
                overflow: hidden;
            }}

            .stDataFrame, div[data-testid="stDataFrame"] {{
                border-radius: 18px;
                overflow: hidden;
                border: 1px solid rgba(139, 90, 59, 0.12);
                box-shadow: 0 10px 24px rgba(91, 58, 41, 0.06);
            }}

            .hero-shell {{
                position: relative;
                overflow: hidden;
                padding: 1.5rem 1.6rem;
                margin-top: 0.35rem;
                margin-bottom: 1rem;
                border-radius: 28px;
                background:
                    radial-gradient(circle at top right, rgba(216, 162, 74, 0.28), transparent 32%),
                    linear-gradient(145deg, rgba(91, 58, 41, 0.96), rgba(124, 74, 45, 0.94));
                color: #fff9f2;
                box-shadow: 0 18px 42px rgba(91, 58, 41, 0.22);
            }}

            .hero-shell h1 {{
                color: #fff9f2;
                margin: 0;
                font-size: 2.55rem;
            }}

            .hero-kicker {{
                display: inline-block;
                margin-bottom: 0.65rem;
                padding: 0.35rem 0.7rem;
                border-radius: 999px;
                background: rgba(255, 249, 242, 0.14);
                border: 1px solid rgba(255, 249, 242, 0.18);
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }}

            .hero-copy {{
                max-width: 760px;
                margin-top: 0.75rem;
                color: rgba(255, 249, 242, 0.88);
                font-size: 1rem;
                line-height: 1.6;
            }}

            .hero-chips {{
                display: flex;
                flex-wrap: wrap;
                gap: 0.55rem;
                margin-top: 1rem;
            }}

            .hero-chip {{
                padding: 0.5rem 0.8rem;
                border-radius: 999px;
                background: rgba(255, 249, 242, 0.1);
                border: 1px solid rgba(255, 249, 242, 0.14);
                font-size: 0.86rem;
                color: #fff9f2;
            }}

            hr {{
                border: none;
                height: 1px;
                background: linear-gradient(90deg, rgba(91,58,41,0), rgba(91,58,41,0.22), rgba(91,58,41,0));
                margin: 1.1rem 0 1.2rem 0;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


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


def safe_period_change(series: pd.Series, periods: int = 30) -> Optional[float]:
    clean_series = series.dropna().reset_index(drop=True)
    if len(clean_series) <= periods:
        return None

    baseline = clean_series.iloc[-periods - 1]
    latest = clean_series.iloc[-1]
    if pd.isna(baseline) or baseline == 0 or pd.isna(latest):
        return None

    return float((latest / baseline) - 1)


def safe_period_diff(series: pd.Series, periods: int = 30) -> Optional[float]:
    clean_series = series.dropna().reset_index(drop=True)
    if len(clean_series) <= periods:
        return None

    baseline = clean_series.iloc[-periods - 1]
    latest = clean_series.iloc[-1]
    if pd.isna(baseline) or pd.isna(latest):
        return None

    return float(latest - baseline)


def initialize_dashboard_state(min_date, max_date):
    if "template_name" not in st.session_state:
        st.session_state["template_name"] = "Custom"

    defaults = apply_template(st.session_state["template_name"])

    if "selected_metric" not in st.session_state:
        st.session_state["selected_metric"] = defaults["metric"]
    if "compare_metric_name" not in st.session_state:
        st.session_state["compare_metric_name"] = defaults["compare"]
    if "time_grain" not in st.session_state:
        st.session_state["time_grain"] = defaults["grain"]
    if "chart_type" not in st.session_state:
        st.session_state["chart_type"] = defaults["chart"]
    if "start_date" not in st.session_state:
        st.session_state["start_date"] = min_date
    if "end_date" not in st.session_state:
        st.session_state["end_date"] = max_date
    if "selected_region" not in st.session_state:
        st.session_state["selected_region"] = "All Regions"


def apply_template_to_state():
    defaults = apply_template(st.session_state["template_name"])
    st.session_state["selected_metric"] = defaults["metric"]
    st.session_state["compare_metric_name"] = defaults["compare"]
    st.session_state["time_grain"] = defaults["grain"]
    st.session_state["chart_type"] = defaults["chart"]


def classify_buy_signal(score: Optional[float]) -> str:
    if score is None or pd.isna(score):
        return "Insufficient Data"
    if score >= 60:
        return "Buy Now"
    if score >= 45:
        return "Watch"
    return "Wait"


def compute_cost_pressure_summary(filtered_df: pd.DataFrame) -> Dict[str, object]:
    ordered_df = filtered_df.sort_values("date_id").reset_index(drop=True)
    latest = ordered_df.iloc[-1]

    coffee_change = safe_period_change(ordered_df["coffee_close"], 30)
    fertilizer_change = safe_period_change(ordered_df["fertilizer_price_index"], 30)
    milk_change = safe_period_change(ordered_df["milk_price_index"], 30)
    brl_change = safe_period_change(ordered_df["brl_usd_exchange_rate"], 30)
    cpi_change = safe_period_change(ordered_df["cpi_value"], 30)
    rate_change = safe_period_diff(ordered_df["fedfunds_value"], 30)

    volatility_median = ordered_df["coffee_30day_volatility"].median()
    volatility_ratio = None
    if pd.notna(latest["coffee_30day_volatility"]) and pd.notna(volatility_median) and volatility_median > 0:
        volatility_ratio = float(latest["coffee_30day_volatility"] / volatility_median)

    score = 0
    drivers: List[str] = []

    if coffee_change is not None:
        if coffee_change >= 0.08:
            score += 3
            drivers.append("coffee futures are up sharply over the last month")
        elif coffee_change >= 0.03:
            score += 2
            drivers.append("coffee futures are trending higher")
        elif coffee_change <= -0.03:
            score -= 1

    if fertilizer_change is not None:
        if fertilizer_change >= 0.05:
            score += 2
            drivers.append("fertilizer costs are rising")
        elif fertilizer_change >= 0.02:
            score += 1
            drivers.append("fertilizer prices are nudging higher")

    if milk_change is not None:
        if milk_change >= 0.04:
            score += 1
            drivers.append("dairy input prices are climbing")
        elif milk_change <= -0.03:
            score -= 1

    if brl_change is not None:
        if brl_change <= -0.03:
            score += 1
            drivers.append("the Brazilian real has strengthened against the dollar")
        elif brl_change >= 0.03:
            score -= 1

    if cpi_change is not None and cpi_change >= 0.004:
        score += 1
        drivers.append("inflation remains firm")

    if rate_change is not None and rate_change >= 0.25:
        score += 1
        drivers.append("interest rates have moved higher")

    if volatility_ratio is not None and volatility_ratio >= 1.15:
        score += 1
        drivers.append("coffee volatility is elevated")

    if score >= 5:
        level = "High"
        color = "#C7522A"
        guidance = "Expect more pressure on bean purchasing decisions and margins."
    elif score >= 2:
        level = "Medium"
        color = "#D4A017"
        guidance = "Watch suppliers and margins closely over the next few weeks."
    else:
        level = "Low"
        color = "#1B7F5B"
        guidance = "Input pressure looks relatively contained right now."

    if not drivers:
        drivers.append("recent market inputs are relatively stable")

    return {
        "level": level,
        "score": score,
        "color": color,
        "guidance": guidance,
        "drivers": drivers[:3],
        "coffee_change": coffee_change,
        "fertilizer_change": fertilizer_change,
        "milk_change": milk_change,
        "brl_change": brl_change,
        "cpi_change": cpi_change,
        "rate_change": rate_change,
    }


def compute_price_review_alert(filtered_df: pd.DataFrame, pressure_summary: Dict[str, object]) -> Dict[str, str]:
    ordered_df = filtered_df.sort_values("date_id").reset_index(drop=True)
    latest_score = ordered_df["buy_opportunity_score"].dropna().iloc[-1] if ordered_df["buy_opportunity_score"].notna().any() else None
    coffee_change = pressure_summary["coffee_change"]
    fertilizer_change = pressure_summary["fertilizer_change"]
    pressure_level = pressure_summary["level"]

    if (
        pressure_level == "High"
        or (coffee_change is not None and coffee_change >= 0.07)
        or (latest_score is not None and latest_score >= 60 and fertilizer_change is not None and fertilizer_change >= 0.03)
    ):
        return {
            "status": "Review Prices Soon",
            "tone": "error",
            "detail": "Consider a 2% to 4% menu review for espresso-heavy drinks if this pressure persists.",
        }

    if pressure_level == "Medium" or (coffee_change is not None and coffee_change >= 0.03):
        return {
            "status": "Monitor Margins",
            "tone": "warning",
            "detail": "Track drink margins weekly and prepare a modest pricing adjustment if costs keep rising.",
        }

    return {
        "status": "Stable for Now",
        "tone": "success",
        "detail": "Current signals do not suggest an urgent menu price change.",
    }


def filter_dataframe(df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    return df[
        (df["date_id"].dt.date >= start_date)
        & (df["date_id"].dt.date <= end_date)
    ].copy()


def prepare_region_scope(df: pd.DataFrame, start_date, end_date, selected_region: str) -> pd.DataFrame:
    filtered_df = filter_dataframe(df, start_date, end_date)
    if filtered_df.empty:
        return filtered_df

    if selected_region != "All Regions":
        return (
            filtered_df.loc[filtered_df["region_name"] == selected_region]
            .sort_values("date_id")
            .reset_index(drop=True)
        )

    numeric_cols = filtered_df.select_dtypes(include="number").columns.tolist()
    region_df = (
        filtered_df.groupby("date_id")[numeric_cols]
        .mean(numeric_only=True)
        .reset_index()
        .sort_values("date_id")
        .reset_index(drop=True)
    )
    region_df["region_name"] = "All Regions"
    region_df["buy_signal"] = region_df["buy_opportunity_score"].apply(classify_buy_signal)
    return region_df


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
            color_discrete_sequence=[PALETTE["espresso"]],
            title=f"Distribution of {selected_metric_col.replace('_', ' ').title()}",
        )
        fig.update_layout(
            template="plotly_white",
            height=360,
            margin=dict(l=20, r=20, t=60, b=20),
            font=dict(family="Manrope", color=PALETTE["ink"]),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig.update_xaxes(showgrid=False, color=PALETTE["ink"])
        fig.update_yaxes(gridcolor="rgba(139, 90, 59, 0.12)", color=PALETTE["ink"])
        st.plotly_chart(fig, width="stretch")
    elif chart_type == "Box":
        box_cols = [selected_metric_col] + ([compare_metric_col] if compare_metric_col else [])
        box_df = result_df[box_cols].melt(var_name="metric", value_name="value").dropna()
        fig = px.box(
            box_df,
            x="metric",
            y="value",
            color="metric",
            color_discrete_sequence=[PALETTE["espresso"], PALETTE["sage"]],
            title="Distribution Range",
            points="outliers",
        )
        fig.update_layout(
            template="plotly_white",
            height=360,
            margin=dict(l=20, r=20, t=60, b=20),
            showlegend=False,
            font=dict(family="Manrope", color=PALETTE["ink"]),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig.update_xaxes(showgrid=False, color=PALETTE["ink"])
        fig.update_yaxes(gridcolor="rgba(139, 90, 59, 0.12)", color=PALETTE["ink"])
        st.plotly_chart(fig, width="stretch")


def render_visual_snapshot(filtered_df: pd.DataFrame):
    ordered_df = filtered_df.sort_values("date_id").reset_index(drop=True).copy()
    ordered_df["month_label"] = ordered_df["date_id"].dt.strftime("%b")
    ordered_df["year"] = ordered_df["date_id"].dt.year.astype(str)

    st.markdown("---")
    st.subheader("Market Snapshot")
    st.caption("A quick visual read of price momentum, input costs, model conviction, and seasonal patterns.")

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
                line=dict(color=PALETTE["espresso"], width=3),
                fill="tozeroy",
                fillcolor="rgba(91, 58, 41, 0.14)",
            )
        )
        price_fig.add_trace(
            go.Scatter(
                x=ordered_df["date_id"],
                y=ordered_df["coffee_7day_ma"],
                mode="lines",
                name="7-Day Average",
                line=dict(color=PALETTE["sage"], width=2, dash="dash"),
            )
        )
        price_fig.update_layout(
            title="Coffee Price Momentum",
            template="plotly_white",
            height=330,
            margin=dict(l=20, r=20, t=60, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            font=dict(family="Manrope", color=PALETTE["ink"]),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        price_fig.update_xaxes(showgrid=False, color=PALETTE["ink"])
        price_fig.update_yaxes(gridcolor="rgba(139, 90, 59, 0.12)", color=PALETTE["ink"])
        st.plotly_chart(price_fig, width="stretch")

    with col2:
        gauge_fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=latest_score,
                number={"suffix": "/100"},
                title={"text": "Buy Score Gauge"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": PALETTE["olive"]},
                    "steps": [
                        {"range": [0, 45], "color": PALETTE["rose"]},
                        {"range": [45, 60], "color": PALETTE["butter"]},
                        {"range": [60, 100], "color": PALETTE["moss"]},
                    ],
                    "threshold": {
                        "line": {"color": PALETTE["ink"], "width": 3},
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
            font=dict(family="Manrope", color=PALETTE["ink"]),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(gauge_fig, width="stretch")

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
            font=dict(family="Manrope", color=PALETTE["ink"]),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(donut_fig, width="stretch")

    col4, col5, col6 = st.columns([1.1, 1.15, 1.0])

    with col4:
        fertilizer_df = ordered_df.dropna(subset=["fertilizer_price_index"]).copy()
        if not fertilizer_df.empty:
            fertilizer_df["fertilizer_30day_avg"] = fertilizer_df["fertilizer_price_index"].rolling(30, min_periods=1).mean()
            fertilizer_fig = go.Figure()
            fertilizer_fig.add_trace(
                go.Scatter(
                    x=fertilizer_df["date_id"],
                    y=fertilizer_df["fertilizer_price_index"],
                    mode="lines",
                    name="Fertilizer Index",
                    line=dict(color=PALETTE["olive"], width=3),
                    fill="tozeroy",
                    fillcolor="rgba(78, 106, 77, 0.16)",
                )
            )
            fertilizer_fig.add_trace(
                go.Scatter(
                    x=fertilizer_df["date_id"],
                    y=fertilizer_df["fertilizer_30day_avg"],
                    mode="lines",
                    name="30-Day Average",
                    line=dict(color=PALETTE["clay"], width=2, dash="dash"),
                )
            )
            fertilizer_fig.update_layout(
                title="Fertilizer Price Trend",
                template="plotly_white",
                height=340,
                margin=dict(l=20, r=20, t=60, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                font=dict(family="Manrope", color=PALETTE["ink"]),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            fertilizer_fig.update_xaxes(showgrid=False, color=PALETTE["ink"])
            fertilizer_fig.update_yaxes(gridcolor="rgba(139, 90, 59, 0.12)", color=PALETTE["ink"])
            st.plotly_chart(fertilizer_fig, width="stretch")

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
                        [0.0, PALETTE["terracotta"]],
                        [0.45, PALETTE["amber"]],
                        [1.0, PALETTE["olive"]],
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
                font=dict(family="Manrope", color=PALETTE["ink"]),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(heatmap_fig, width="stretch")

    with col6:
        fx_df = ordered_df.dropna(subset=["brl_usd_exchange_rate"]).copy()
        if not fx_df.empty:
            fx_df["fx_30day_avg"] = fx_df["brl_usd_exchange_rate"].rolling(30, min_periods=1).mean()
            fx_fig = go.Figure()
            fx_fig.add_trace(
                go.Scatter(
                    x=fx_df["date_id"],
                    y=fx_df["brl_usd_exchange_rate"],
                    mode="lines",
                    name="BRL/USD",
                    line=dict(color=PALETTE["clay"], width=3),
                    fill="tozeroy",
                    fillcolor="rgba(163, 93, 45, 0.14)",
                )
            )
            fx_fig.add_trace(
                go.Scatter(
                    x=fx_df["date_id"],
                    y=fx_df["fx_30day_avg"],
                    mode="lines",
                    name="30-Day Average",
                    line=dict(color=PALETTE["sage"], width=2, dash="dash"),
                )
            )
            fx_fig.update_layout(
                title="Brazil FX Pressure",
                template="plotly_white",
                height=340,
                margin=dict(l=20, r=20, t=60, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                font=dict(family="Manrope", color=PALETTE["ink"]),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            fx_fig.update_xaxes(showgrid=False, color=PALETTE["ink"])
            fx_fig.update_yaxes(gridcolor="rgba(139, 90, 59, 0.12)", color=PALETTE["ink"])
            st.plotly_chart(fx_fig, width="stretch")


def compute_buy_score_drivers(filtered_df: pd.DataFrame) -> pd.DataFrame:
    ordered_df = filtered_df.sort_values("date_id").reset_index(drop=True)
    latest = ordered_df.iloc[-1]

    price_vs_ma = 0.0
    if pd.notna(latest["coffee_30day_ma"]) and latest["coffee_30day_ma"] != 0:
        price_vs_ma = float((latest["coffee_close"] / latest["coffee_30day_ma"]) - 1)

    short_return = safe_period_change(ordered_df["coffee_close"], 7) or 0.0
    volatility_baseline = ordered_df["coffee_30day_volatility"].median()
    volatility_ratio = 1.0
    if (
        pd.notna(latest["coffee_30day_volatility"])
        and pd.notna(volatility_baseline)
        and volatility_baseline > 0
    ):
        volatility_ratio = float(latest["coffee_30day_volatility"] / volatility_baseline)

    recent_rain = ordered_df["precipitation"].tail(7).mean()
    monthly_rain = ordered_df["precipitation"].tail(30).mean()
    rain_gap = 0.0
    if pd.notna(recent_rain) and pd.notna(monthly_rain) and monthly_rain > 0:
        rain_gap = float((recent_rain / monthly_rain) - 1)

    temp_baseline = ordered_df["avg_temp"].tail(60).mean()
    temp_gap = 0.0
    if pd.notna(temp_baseline) and pd.notna(latest["avg_temp"]):
        temp_gap = float(latest["avg_temp"] - temp_baseline)

    fertilizer_change = safe_period_change(ordered_df["fertilizer_price_index"], 30) or 0.0
    milk_change = safe_period_change(ordered_df["milk_price_index"], 30) or 0.0
    brl_change = safe_period_change(ordered_df["brl_usd_exchange_rate"], 30) or 0.0
    cpi_change = safe_period_change(ordered_df["cpi_value"], 30) or 0.0
    rate_change = safe_period_diff(ordered_df["fedfunds_value"], 30) or 0.0

    return pd.DataFrame(
        [
            {
                "driver": "Price Momentum",
                "impact": max(min((price_vs_ma * 180) + (short_return * 110) + ((volatility_ratio - 1) * 8), 22), -22),
                "note": "Tracks coffee versus its 30-day trend, short-term price change, and volatility backdrop.",
            },
            {
                "driver": "Weather Stress",
                "impact": max(min(((-rain_gap) * 14) + (temp_gap * 1.3), 18), -18),
                "note": "Highlights dry or hotter conditions across the Brazil weather regions feeding the dashboard.",
            },
            {
                "driver": "Input Costs",
                "impact": max(min((fertilizer_change * 130) + (milk_change * 80), 20), -20),
                "note": "Summarizes agricultural and cafe input-cost pressure from fertilizer and milk proxies.",
            },
            {
                "driver": "Macro & FX",
                "impact": max(min((cpi_change * 700) - (rate_change * 4.5) - (brl_change * 120), 20), -20),
                "note": "Blends inflation, rates, and BRL/USD moves that can influence coffee export and financing conditions.",
            },
        ]
    )


def render_buy_score_driver_panel(filtered_df: pd.DataFrame):
    ordered_df = filtered_df.sort_values("date_id").reset_index(drop=True)
    latest_score = ordered_df["buy_opportunity_score"].dropna().iloc[-1] if ordered_df["buy_opportunity_score"].notna().any() else None
    drivers_df = compute_buy_score_drivers(ordered_df)
    drivers_df["color"] = drivers_df["impact"].apply(
        lambda value: PALETTE["olive"] if value >= 0 else PALETTE["terracotta"]
    )

    st.markdown("---")
    st.subheader("Buy Score Drivers")
    st.caption(
        "Directional support behind the current buy score. These are explanatory signal buckets built from the latest market inputs, not exact model coefficients."
    )

    col1, col2 = st.columns([1.55, 1.0])

    with col1:
        fig = go.Figure(
            go.Bar(
                x=drivers_df["impact"],
                y=drivers_df["driver"],
                orientation="h",
                marker_color=drivers_df["color"],
                text=[f"{impact:+.1f}" for impact in drivers_df["impact"]],
                textposition="outside",
                hovertemplate="%{y}<br>Impact %{x:+.1f}<extra></extra>",
            )
        )
        fig.update_layout(
            template="plotly_white",
            height=320,
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis_title="Directional Impact",
            font=dict(family="Manrope", color=PALETTE["ink"]),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig.update_xaxes(
            range=[-24, 24],
            zeroline=True,
            zerolinecolor="rgba(91, 58, 41, 0.35)",
            gridcolor="rgba(139, 90, 59, 0.12)",
            color=PALETTE["ink"],
        )
        fig.update_yaxes(
            showgrid=False,
            categoryorder="array",
            categoryarray=drivers_df["driver"][::-1],
            color=PALETTE["ink"],
        )
        st.plotly_chart(fig, width="stretch")

    with col2:
        if latest_score is not None:
            st.metric("Latest Buy Score", f"{latest_score:.1f}/100")
            st.write(f"**Signal:** {classify_buy_signal(latest_score)}")
        else:
            st.metric("Latest Buy Score", "N/A")
            st.caption("More history is needed before a stable score can be shown.")

        for row in drivers_df.itertuples(index=False):
            direction = "supportive" if row.impact >= 0 else "softening"
            st.write(f"**{row.driver}:** {direction} ({row.impact:+.1f})")
            st.caption(row.note)


def render_owner_action_center(filtered_df: pd.DataFrame):
    ordered_df = filtered_df.sort_values("date_id").reset_index(drop=True)
    latest = ordered_df.iloc[-1]
    latest_score = latest["buy_opportunity_score"]
    pressure_summary = compute_cost_pressure_summary(ordered_df)
    price_alert = compute_price_review_alert(ordered_df, pressure_summary)

    st.markdown("---")
    st.subheader("Owner Action Center")
    st.caption("Three fast decision views for purchasing, cost pressure, and menu pricing.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Purchasing Recommendation")
        if pd.isna(latest_score):
            st.metric("Buy Score", "N/A")
            st.caption("Not enough history yet for a stable recommendation.")
        else:
            score_history = ordered_df["buy_opportunity_score"].dropna()
            score_delta = latest_score - score_history.iloc[-8] if len(score_history) >= 8 else None
            if score_delta is None:
                st.metric("Buy Score", f"{latest_score:.1f}/100")
            else:
                st.metric("Buy Score", f"{latest_score:.1f}/100", f"{score_delta:+.1f} vs 7 days ago")
            st.write(f"**Signal:** {latest['buy_signal']}")
            st.caption(build_buy_opportunity_context(ordered_df))

    with col2:
        st.markdown("#### Cost Pressure Summary")
        st.metric("Pressure Level", pressure_summary["level"])
        st.caption(pressure_summary["guidance"])
        for driver in pressure_summary["drivers"]:
            st.write(f"- {driver.capitalize()}.")

    with col3:
        st.markdown("#### Menu Price Review")
        st.metric("Pricing Alert", price_alert["status"])
        if price_alert["tone"] == "error":
            st.error(price_alert["detail"])
        elif price_alert["tone"] == "warning":
            st.warning(price_alert["detail"])
        else:
            st.success(price_alert["detail"])


def render_margin_impact_calculator(filtered_df: pd.DataFrame):
    ordered_df = filtered_df.sort_values("date_id").reset_index(drop=True)
    latest = ordered_df.iloc[-1]
    latest_coffee_dollars = float(latest["coffee_close"]) / 100.0
    market_change = safe_period_change(ordered_df["coffee_close"], 30)
    default_bean_cost = round(max(latest_coffee_dollars * 3.2, 10.0), 2)
    default_projected_change = round((market_change or 0.03) * 100.0, 1)

    st.markdown("---")
    st.subheader("Margin Impact Calculator")
    st.caption("Quick simulator for how bean-cost moves could affect drink margin. This is a simple bean-cost view, not a full P&L.")

    input_col1, input_col2, input_col3, input_col4, input_col5 = st.columns(5)
    bean_cost_per_lb = input_col1.number_input(
        "Roasted Beans Cost / lb",
        min_value=0.0,
        value=default_bean_cost,
        step=0.25,
    )
    grams_per_drink = input_col2.number_input(
        "Beans per Drink (g)",
        min_value=1.0,
        value=18.0,
        step=0.5,
    )
    avg_drink_price = input_col3.number_input(
        "Average Drink Price",
        min_value=0.0,
        value=5.75,
        step=0.1,
    )
    drinks_per_day = input_col4.number_input(
        "Drinks per Day",
        min_value=1,
        value=120,
        step=5,
    )
    projected_cost_change_pct = input_col5.number_input(
        "Projected Bean Cost Change %",
        value=default_projected_change,
        step=0.5,
    )

    pounds_per_drink = grams_per_drink / 453.592
    current_cost_per_drink = bean_cost_per_lb * pounds_per_drink
    projected_cost_per_drink = current_cost_per_drink * (1 + projected_cost_change_pct / 100.0)
    daily_cost_impact = (projected_cost_per_drink - current_cost_per_drink) * drinks_per_day
    monthly_cost_impact = daily_cost_impact * 30
    price_lift_needed = max(projected_cost_per_drink - current_cost_per_drink, 0)
    suggested_price = avg_drink_price + price_lift_needed

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("Current Bean Cost / Drink", f"${current_cost_per_drink:.2f}")
    metric_col2.metric("Projected Bean Cost / Drink", f"${projected_cost_per_drink:.2f}")
    metric_col3.metric("Monthly Margin Impact", f"${monthly_cost_impact:,.0f}")
    metric_col4.metric("Price Lift to Offset", f"${price_lift_needed:.2f}")

    st.caption(
        f"If bean costs move by {projected_cost_change_pct:.1f}%, keeping bean margin flat would move an average ${avg_drink_price:.2f} drink to about ${suggested_price:.2f}."
    )


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

    milk_window = ordered_df["milk_price_index"].dropna().tail(31)
    if len(milk_window) >= 2 and milk_window.iloc[0] != 0:
        milk_change = (milk_window.iloc[-1] / milk_window.iloc[0]) - 1
        if milk_change > 0.02:
            context_notes.append("milk-related cafe input costs are trending higher")
        elif milk_change < -0.02:
            context_notes.append("milk-related cafe input costs have cooled recently")

    brl_window = ordered_df["brl_usd_exchange_rate"].dropna().tail(31)
    if len(brl_window) >= 2 and brl_window.iloc[0] != 0:
        brl_change = (brl_window.iloc[-1] / brl_window.iloc[0]) - 1
        if brl_change < -0.02:
            context_notes.append("the Brazilian real has strengthened, which can support higher coffee prices")
        elif brl_change > 0.02:
            context_notes.append("the Brazilian real has weakened, which can soften export-side price pressure")

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
        return "The score is based on recent coffee momentum, weather, fertilizer costs, milk-input pressure, inflation, exchange-rate moves, and interest-rate conditions."

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
    latest_brl_usd = float(latest["brl_usd_exchange_rate"])
    latest_milk_index = float(latest["milk_price_index"])
    latest_score = latest["buy_opportunity_score"]

    st.subheader("Key Metrics")
    top_col1, top_col2, top_col3, top_col4 = st.columns(4)
    bottom_col1, bottom_col2, bottom_col3, bottom_col4 = st.columns(4)

    top_col1.metric(
        "Coffee Futures Close",
        f"{latest_coffee_cents:.2f} cents/lb",
        help="End-of-day coffee futures closing price.",
    )
    top_col1.caption(f"≈ ${latest_coffee_dollars:.4f} per lb")

    top_col2.metric(
        "7-Day Avg Futures Price",
        f"{latest_ma_cents:.2f} cents/lb",
        help="Average of the last 7 daily coffee futures closing prices.",
    )
    top_col2.caption(f"≈ ${latest_ma_dollars:.4f} per lb")

    top_col3.metric(
        "Buy Opportunity Score",
        "N/A" if pd.isna(latest_score) else f"{latest_score:.1f}/100",
        help="Experimental 7-day directional score built during the ETL pipeline.",
    )
    top_col3.caption(f"Signal: {classify_buy_signal(latest_score)}")

    top_col4.metric(
        "Fertilizer Price Index",
        f"{latest_fertilizer_index:.2f}",
        help="FRED producer price index for fertilizer manufacturing, used here as an agricultural input-cost proxy.",
    )

    bottom_col1.metric(
        "Avg Temperature",
        f"{avg_temp_period:.2f} °C",
        help="Average daily temperature across the selected period.",
    )

    bottom_col2.metric(
        "Total Precipitation",
        f"{total_precip_period:.2f} mm",
        help="Total rainfall across the selected period.",
    )

    bottom_col3.metric(
        "BRL/USD Exchange Rate",
        f"{latest_brl_usd:.3f}",
        help="Brazilian real to U.S. dollar exchange rate from FRED.",
    )
    bottom_col3.caption(
        f"Milk Index: {latest_milk_index:.2f} | Fed Funds: {latest['fedfunds_value']:.2f}% | CPI: {latest['cpi_value']:.2f}"
    )

    bottom_col4.metric(
        "Selected Scope",
        latest.get("region_name", "All Regions"),
        help="Region or multi-region scope currently shown in the dashboard.",
    )
    bottom_col4.caption("The buy score and weather averages reflect this scope.")


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
    st.line_chart(
        filtered_df.set_index("date_id")[
            ["cpi_value", "fedfunds_value", "fertilizer_price_index", "brl_usd_exchange_rate", "milk_price_index"]
        ]
    )

    st.caption("Experimental 7-day buy-opportunity score.")
    st.line_chart(filtered_df.set_index("date_id")[["buy_opportunity_score"]])


def main():
    inject_theme()
    df = load_warehouse_data()

    if df.empty:
        st.error("No data found in fact_market_features.")
        st.stop()

    st.markdown(
        """
        <div class="hero-shell">
            <div class="hero-kicker">Coffee Shop Owner Dashboard</div>
            <h1>Coffee Market Intelligence Dashboard</h1>
            <div class="hero-copy">
                Track coffee buying pressure, menu pricing risk, and market momentum in one owner-friendly workspace.
                The dashboard blends commodity signals, fertilizer pressure, and an experimental buy score to support more confident purchasing decisions.
            </div>
            <div class="hero-chips">
                <div class="hero-chip">Purchasing Signals</div>
                <div class="hero-chip">Margin Awareness</div>
                <div class="hero-chip">Input Cost Pressure</div>
                <div class="hero-chip">Visual Snapshot</div>
            </div>
        </div>
        """
        ,
        unsafe_allow_html=True,
    )
    st.caption("Use the Information page in the sidebar for source notes, metric definitions, and ETL explanation.")

    min_date = df["date_id"].min().date()
    max_date = df["date_id"].max().date()
    initialize_dashboard_state(min_date, max_date)
    region_options = ["All Regions"] + sorted(df["region_name"].dropna().unique().tolist())
    if st.session_state["selected_region"] not in region_options:
        st.session_state["selected_region"] = "All Regions"

    start_date = st.session_state["start_date"]
    end_date = st.session_state["end_date"]
    if start_date < min_date or start_date > max_date:
        start_date = min_date
        st.session_state["start_date"] = min_date
    if end_date < min_date or end_date > max_date:
        end_date = max_date
        st.session_state["end_date"] = max_date
    if start_date > end_date:
        start_date = min_date
        end_date = max_date
        st.session_state["start_date"] = min_date
        st.session_state["end_date"] = max_date

    st.markdown("---")
    st.subheader("Dashboard Scope")
    scope_col1, scope_col2, scope_col3 = st.columns(3)
    scope_col1.selectbox("Region View", region_options, key="selected_region")
    scope_col2.date_input("Start Date", min_value=min_date, max_value=max_date, key="start_date")
    scope_col3.date_input("End Date", min_value=min_date, max_value=max_date, key="end_date")

    start_date = st.session_state["start_date"]
    end_date = st.session_state["end_date"]
    selected_region = st.session_state["selected_region"]
    filtered_df = prepare_region_scope(df, start_date, end_date, selected_region)
    if filtered_df.empty:
        st.warning("No data found for the selected date range.")
        st.stop()

    st.caption(
        f"Current scope: **{selected_region}** from **{start_date}** to **{end_date}**. "
        "When All Regions is selected, weather and buy-score inputs are averaged across the Brazil region set."
    )

    render_owner_action_center(filtered_df)
    render_buy_score_driver_panel(filtered_df)
    render_margin_impact_calculator(filtered_df)
    render_kpis(filtered_df)
    render_visual_snapshot(filtered_df)

    st.markdown("---")
    st.subheader("Quick Analysis Templates")
    st.selectbox(
        "Choose a common analysis question",
        list(TEMPLATES.keys()),
        key="template_name",
        on_change=apply_template_to_state,
    )

    st.markdown("---")
    st.subheader("Explore the Warehouse")

    col1, col2, col3 = st.columns(3)
    col1.selectbox("Primary Metric", list(METRIC_OPTIONS.keys()), key="selected_metric")
    col2.selectbox("Compare Against", ["None"] + list(METRIC_OPTIONS.keys()), key="compare_metric_name")
    col3.selectbox("Time Grain", ["Daily", "Weekly", "Monthly"], key="time_grain")

    chart_options = ["Line", "Bar", "Area", "Histogram", "Box"]
    if st.session_state["compare_metric_name"] != "None":
        chart_options.append("Scatter")
    if st.session_state["chart_type"] not in chart_options:
        st.session_state["chart_type"] = "Line"
    st.selectbox("Chart Type", chart_options, key="chart_type")

    start_date = st.session_state["start_date"]
    end_date = st.session_state["end_date"]
    selected_region = st.session_state["selected_region"]
    if start_date > end_date:
        st.error("Start Date must be before or equal to End Date.")
        st.stop()

    filtered_df = prepare_region_scope(df, start_date, end_date, selected_region)
    if filtered_df.empty:
        st.warning("No data found for the selected date range.")
        st.stop()

    selected_metric = st.session_state["selected_metric"]
    compare_metric_name = st.session_state["compare_metric_name"]
    time_grain = st.session_state["time_grain"]
    chart_type = st.session_state["chart_type"]

    selected_metric_col = METRIC_OPTIONS[selected_metric]
    compare_metric_col = METRIC_OPTIONS.get(compare_metric_name) if compare_metric_name != "None" else None
    result_df = aggregate_dataframe(filtered_df, selected_metric_col, compare_metric_col, time_grain)

    st.info(
        f"This query analyzes {selected_metric.lower()} for {selected_region.lower()}"
        + (f" against {compare_metric_name.lower()}" if compare_metric_name != "None" else "")
        + f" using {time_grain.lower()} aggregation for the selected date range."
    )

    st.markdown("---")
    st.subheader("Query Result")
    st.write(
        f"Showing **{selected_metric}**"
        + (f" compared with **{compare_metric_name}**" if compare_metric_col else "")
        + f" for **{selected_region}** at **{time_grain.lower()}** granularity from **{start_date}** to **{end_date}**."
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
