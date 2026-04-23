import os
from typing import Dict, Optional

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

st.set_page_config(page_title="Owner Planner", layout="wide")

OPS_PALETTE = {
    "ink": "#2F241F",
    "espresso": "#5B3A29",
    "mocha": "#8A5A3B",
    "oat": "#F6F0E8",
    "cream": "#FBF7F2",
    "sage": "#6F8A6D",
    "olive": "#4E6A4D",
    "terracotta": "#C56C4B",
    "amber": "#D8A24A",
    "mist": "#DDD1C3",
}

MARKET_QUERY = """
SELECT
    date_id,
    AVG(coffee_close) AS coffee_close,
    AVG(coffee_30day_ma) AS coffee_30day_ma,
    AVG(coffee_30day_volatility) AS coffee_30day_volatility,
    AVG(fertilizer_price_index) AS fertilizer_price_index,
    AVG(milk_price_index) AS milk_price_index,
    AVG(cpi_value) AS cpi_value,
    AVG(fedfunds_value) AS fedfunds_value,
    AVG(buy_opportunity_score) AS buy_opportunity_score
FROM fact_market_features
GROUP BY date_id
ORDER BY date_id
"""

LATEST_PRICE_QUERY = """
SELECT
    s.supplier_id,
    s.supplier_name,
    s.origin_region,
    s.lead_time_days,
    s.min_order_lbs,
    i.ingredient_id,
    i.ingredient_name,
    i.ingredient_category,
    p.price_date,
    p.unit_cost,
    p.unit
FROM supplier_price_history p
JOIN (
    SELECT supplier_id, ingredient_id, MAX(price_date) AS max_price_date
    FROM supplier_price_history
    GROUP BY supplier_id, ingredient_id
) latest
    ON p.supplier_id = latest.supplier_id
    AND p.ingredient_id = latest.ingredient_id
    AND p.price_date = latest.max_price_date
JOIN suppliers s
    ON p.supplier_id = s.supplier_id
JOIN ingredients i
    ON p.ingredient_id = i.ingredient_id
WHERE s.is_active = TRUE
"""

MENU_QUERY = """
SELECT
    m.item_id,
    m.item_name,
    m.category,
    m.menu_price,
    m.size_oz,
    m.daily_units,
    r.ingredient_id,
    r.quantity_per_item,
    r.quantity_unit,
    i.ingredient_name,
    i.ingredient_category
FROM menu_items m
JOIN recipes r
    ON m.item_id = r.item_id
JOIN ingredients i
    ON r.ingredient_id = i.ingredient_id
WHERE m.is_active = TRUE
ORDER BY m.item_name, r.recipe_id
"""

INVENTORY_QUERY = """
SELECT
    ip.ingredient_id,
    i.ingredient_name,
    i.ingredient_category,
    ip.snapshot_date,
    ip.on_hand_qty,
    ip.reorder_point_qty,
    ip.target_qty,
    ip.quantity_unit
FROM inventory_positions ip
JOIN ingredients i
    ON ip.ingredient_id = i.ingredient_id
"""


def inject_owner_theme():
    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600;700&family=Manrope:wght@400;500;600;700&display=swap');

            .stApp {{
                background:
                    radial-gradient(circle at top left, rgba(216, 162, 74, 0.16), transparent 25%),
                    linear-gradient(180deg, #fcf8f3 0%, #f5ede3 48%, #faf4ec 100%);
                color: {OPS_PALETTE["ink"]};
                font-family: 'Manrope', sans-serif;
            }}

            .block-container {{
                max-width: 1440px;
                padding-top: 4.2rem;
                padding-bottom: 3rem;
            }}

            h1, h2, h3 {{
                font-family: 'Fraunces', serif;
                color: {OPS_PALETTE["espresso"]};
                letter-spacing: -0.02em;
            }}

            [data-testid="stMetric"] {{
                background: rgba(251, 247, 242, 0.84);
                border: 1px solid rgba(139, 90, 59, 0.14);
                border-radius: 20px;
                box-shadow: 0 14px 28px rgba(91, 58, 41, 0.08);
            }}

            .owner-hero {{
                padding: 1.4rem 1.6rem;
                border-radius: 28px;
                background:
                    radial-gradient(circle at top right, rgba(216, 162, 74, 0.24), transparent 30%),
                    linear-gradient(145deg, rgba(91, 58, 41, 0.97), rgba(124, 74, 45, 0.94));
                color: #fff9f2;
                box-shadow: 0 18px 40px rgba(91, 58, 41, 0.2);
                margin-bottom: 1rem;
            }}

            .owner-hero h1 {{
                color: #fff9f2;
                margin-bottom: 0.35rem;
            }}

            .owner-chip {{
                display: inline-block;
                margin-right: 0.5rem;
                margin-top: 0.6rem;
                padding: 0.45rem 0.75rem;
                border-radius: 999px;
                background: rgba(255, 249, 242, 0.12);
                border: 1px solid rgba(255, 249, 242, 0.16);
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def mysql_engine():
    return create_engine(
        f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
        f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DB')}"
    )


def postgres_engine():
    return create_engine(
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )


@st.cache_data(show_spinner=False)
def load_market_data() -> pd.DataFrame:
    df = pd.read_sql(MARKET_QUERY, postgres_engine())
    df["date_id"] = pd.to_datetime(df["date_id"])
    return df


@st.cache_data(show_spinner=False)
def load_supplier_prices() -> pd.DataFrame:
    df = pd.read_sql(LATEST_PRICE_QUERY, mysql_engine())
    df["price_date"] = pd.to_datetime(df["price_date"])
    return df


@st.cache_data(show_spinner=False)
def load_menu_recipes() -> pd.DataFrame:
    return pd.read_sql(MENU_QUERY, mysql_engine())


@st.cache_data(show_spinner=False)
def load_inventory() -> pd.DataFrame:
    df = pd.read_sql(INVENTORY_QUERY, mysql_engine())
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
    return df


def safe_period_change(series: pd.Series, periods: int = 30) -> Optional[float]:
    clean_series = series.dropna().reset_index(drop=True)
    if len(clean_series) <= periods:
        return None

    baseline = clean_series.iloc[-periods - 1]
    latest = clean_series.iloc[-1]
    if pd.isna(baseline) or baseline == 0 or pd.isna(latest):
        return None

    return float((latest / baseline) - 1)


def unit_cost_for_recipe(quantity: float, recipe_unit: str, unit_cost: float, purchase_unit: str) -> float:
    if recipe_unit == purchase_unit:
        return float(quantity) * float(unit_cost)
    if recipe_unit == "g" and purchase_unit == "lb":
        return (float(quantity) / 453.592) * float(unit_cost)
    raise ValueError(f"Unsupported unit conversion from {recipe_unit} to {purchase_unit}")


def build_current_cost_lookup(price_df: pd.DataFrame) -> Dict[int, Dict[str, object]]:
    lookup: Dict[int, Dict[str, object]] = {}
    for _, row in price_df.sort_values(["ingredient_id", "unit_cost"]).iterrows():
        ingredient_id = int(row["ingredient_id"])
        if ingredient_id not in lookup:
            lookup[ingredient_id] = {
                "ingredient_name": row["ingredient_name"],
                "ingredient_category": row["ingredient_category"],
                "unit_cost": float(row["unit_cost"]),
                "unit": row["unit"],
                "supplier_name": row["supplier_name"],
                "lead_time_days": int(row["lead_time_days"]),
                "min_order_lbs": float(row["min_order_lbs"]),
            }
    return lookup


def build_menu_cost_table(
    recipes_df: pd.DataFrame,
    cost_lookup: Dict[int, Dict[str, object]],
    bean_change_pct: float,
    dairy_change_pct: float,
    flavor_change_pct: float,
    packaging_change_pct: float,
    sales_multiplier: float,
) -> pd.DataFrame:
    working_df = recipes_df.copy()
    current_costs = []
    projected_costs = []

    for row in working_df.itertuples(index=False):
        cost_info = cost_lookup.get(int(row.ingredient_id))
        if not cost_info:
            current_costs.append(0.0)
            projected_costs.append(0.0)
            continue

        current_cost = unit_cost_for_recipe(
            quantity=row.quantity_per_item,
            recipe_unit=row.quantity_unit,
            unit_cost=cost_info["unit_cost"],
            purchase_unit=cost_info["unit"],
        )

        multiplier = 1.0
        category = row.ingredient_category
        if category == "beans":
            multiplier += bean_change_pct / 100.0
        elif category == "dairy":
            multiplier += dairy_change_pct / 100.0
        elif category in {"syrup", "sauce"}:
            multiplier += flavor_change_pct / 100.0
        elif category == "packaging":
            multiplier += packaging_change_pct / 100.0

        current_costs.append(current_cost)
        projected_costs.append(current_cost * multiplier)

    working_df["current_cost"] = current_costs
    working_df["projected_cost"] = projected_costs

    grouped = (
        working_df.groupby(["item_id", "item_name", "category", "menu_price", "daily_units"], as_index=False)[
            ["current_cost", "projected_cost"]
        ]
        .sum()
        .sort_values("menu_price", ascending=False)
    )

    grouped["projected_daily_units"] = (grouped["daily_units"] * sales_multiplier).round().astype(int)
    grouped["current_margin_dollars"] = grouped["menu_price"] - grouped["current_cost"]
    grouped["projected_margin_dollars"] = grouped["menu_price"] - grouped["projected_cost"]
    grouped["current_margin_pct"] = grouped["current_margin_dollars"] / grouped["menu_price"]
    grouped["projected_margin_pct"] = grouped["projected_margin_dollars"] / grouped["menu_price"]
    grouped["daily_margin_impact"] = (
        (grouped["projected_margin_dollars"] - grouped["current_margin_dollars"]) * grouped["projected_daily_units"]
    )
    grouped["price_to_hold_margin"] = grouped["menu_price"] + (grouped["projected_cost"] - grouped["current_cost"])

    return grouped


def render_purchasing_planner(market_df: pd.DataFrame, price_df: pd.DataFrame, recipes_df: pd.DataFrame, inventory_df: pd.DataFrame):
    latest = market_df.sort_values("date_id").iloc[-1]
    bean_suppliers = price_df.loc[price_df["ingredient_category"] == "beans"].copy().sort_values("unit_cost")
    bean_inventory = inventory_df.loc[inventory_df["ingredient_category"] == "beans"].iloc[0]
    bean_usage_df = recipes_df.loc[recipes_df["ingredient_category"] == "beans"].copy()

    market_bean_change = safe_period_change(market_df["coffee_close"], 30)
    default_sales_multiplier = 1.00

    st.subheader("Purchasing Planner")
    st.caption("Turn warehouse signals into a concrete bean ordering plan using supplier data, shop recipes, and current inventory.")

    control_col1, control_col2, control_col3, control_col4 = st.columns(4)
    supplier_name = control_col1.selectbox("Bean Supplier", bean_suppliers["supplier_name"].tolist(), index=0)
    planning_horizon_days = control_col2.slider("Planning Horizon (days)", min_value=7, max_value=42, value=21, step=7)
    sales_multiplier = control_col3.slider("Sales Volume Multiplier", min_value=0.70, max_value=1.50, value=default_sales_multiplier, step=0.05)
    target_days_supply = control_col4.slider("Target Days of Supply", min_value=10, max_value=35, value=21, step=1)

    supplier_row = bean_suppliers.loc[bean_suppliers["supplier_name"] == supplier_name].iloc[0]

    projected_daily_bean_grams = float((bean_usage_df["quantity_per_item"] * bean_usage_df["daily_units"]).sum()) * sales_multiplier
    projected_weekly_bean_lbs = (projected_daily_bean_grams * 7.0) / 453.592
    daily_bean_lbs = projected_weekly_bean_lbs / 7.0
    on_hand_lbs = float(bean_inventory["on_hand_qty"])
    days_of_supply = on_hand_lbs / daily_bean_lbs if daily_bean_lbs > 0 else 0.0

    lead_time_days = int(supplier_row["lead_time_days"])
    min_order_lbs = float(supplier_row["min_order_lbs"])
    current_price = float(supplier_row["unit_cost"])
    expected_price_move_pct = max((market_bean_change or 0.0) * 100.0, 0.0)
    expected_delayed_cost = current_price * (1.0 + (expected_price_move_pct / 100.0) * (lead_time_days / 30.0))
    suggested_order_lbs = max((daily_bean_lbs * target_days_supply) - on_hand_lbs, min_order_lbs)
    projected_arrival_inventory = on_hand_lbs - (daily_bean_lbs * lead_time_days) + suggested_order_lbs

    if days_of_supply <= lead_time_days + 3 or (pd.notna(latest["buy_opportunity_score"]) and latest["buy_opportunity_score"] >= 60):
        action = "Buy This Week"
        tone = st.error
        detail = "Inventory coverage is getting tight relative to supplier lead time, and market signals are supportive of earlier buying."
    elif days_of_supply <= lead_time_days + 7 or (pd.notna(latest["buy_opportunity_score"]) and latest["buy_opportunity_score"] >= 45):
        action = "Plan Next Order"
        tone = st.warning
        detail = "Coverage is still workable, but the shop should line up the next order before the buffer narrows further."
    else:
        action = "Monitor for Now"
        tone = st.success
        detail = "Coverage looks comfortable enough to wait while continuing to watch the market and supplier quotes."

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("Recommended Action", action)
    metric_col2.metric("Days of Bean Supply", f"{days_of_supply:.1f}")
    metric_col3.metric("Suggested Order Size", f"{suggested_order_lbs:.1f} lb")
    metric_col4.metric("Supplier Price", f"${current_price:.2f}/lb")

    tone(detail)

    planner_col1, planner_col2 = st.columns([1.35, 1.0])

    with planner_col1:
        supplier_view = bean_suppliers[[
            "supplier_name",
            "origin_region",
            "lead_time_days",
            "min_order_lbs",
            "unit_cost",
            "price_date",
        ]].copy()
        supplier_view["expected_cost_if_delayed"] = supplier_view.apply(
            lambda row: float(row["unit_cost"]) * (1.0 + (expected_price_move_pct / 100.0) * (float(row["lead_time_days"]) / 30.0)),
            axis=1,
        )
        supplier_view = supplier_view.rename(
            columns={
                "supplier_name": "Supplier",
                "origin_region": "Origin",
                "lead_time_days": "Lead Time (days)",
                "min_order_lbs": "Min Order (lb)",
                "unit_cost": "Current $/lb",
                "price_date": "Quoted On",
                "expected_cost_if_delayed": "Estimated $/lb if delayed",
            }
        )
        st.markdown("#### Supplier Comparison")
        st.dataframe(supplier_view, width="stretch", hide_index=True)

    with planner_col2:
        st.markdown("#### Planner Notes")
        st.write(f"**Projected weekly bean usage:** {projected_weekly_bean_lbs:.1f} lb")
        st.write(f"**Current on-hand inventory:** {on_hand_lbs:.1f} lb")
        st.write(f"**Inventory on supplier arrival:** {projected_arrival_inventory:.1f} lb")
        st.write(f"**Lead time:** {lead_time_days} days")
        st.write(f"**Buy score backdrop:** {latest['buy_opportunity_score']:.1f}/100" if pd.notna(latest["buy_opportunity_score"]) else "**Buy score backdrop:** N/A")
        st.caption(
            "The suggested order size tries to restore the target days of supply while respecting the supplier minimum order."
        )

    horizon_cost = suggested_order_lbs * current_price
    delayed_cost = suggested_order_lbs * expected_delayed_cost
    st.caption(
        f"Ordering {suggested_order_lbs:.1f} lb now would cost about ${horizon_cost:,.0f}. Waiting through the supplier lead time could move that to about ${delayed_cost:,.0f} if current market pressure persists."
    )


def render_margin_studio(market_df: pd.DataFrame, price_df: pd.DataFrame, recipes_df: pd.DataFrame):
    cost_lookup = build_current_cost_lookup(price_df)
    default_bean_change = round((safe_period_change(market_df["coffee_close"], 30) or 0.03) * 100.0, 1)
    default_dairy_change = round((safe_period_change(market_df["milk_price_index"], 30) or 0.02) * 100.0, 1)
    default_flavor_change = round((safe_period_change(market_df["cpi_value"], 30) or 0.01) * 100.0, 1)

    st.markdown("---")
    st.subheader("Menu Margin Studio")
    st.caption("Estimate current and projected gross margin by menu item using seeded recipe data and the latest operational input costs.")

    control_col1, control_col2, control_col3, control_col4, control_col5 = st.columns(5)
    bean_change_pct = control_col1.number_input("Bean Cost Change %", value=default_bean_change, step=0.5)
    dairy_change_pct = control_col2.number_input("Milk Cost Change %", value=default_dairy_change, step=0.5)
    flavor_change_pct = control_col3.number_input("Syrup and Sauce Change %", value=default_flavor_change, step=0.5)
    packaging_change_pct = control_col4.number_input("Packaging Change %", value=2.0, step=0.5)
    sales_multiplier = control_col5.number_input("Projected Sales Multiplier", min_value=0.50, value=1.00, step=0.05)

    margin_df = build_menu_cost_table(
        recipes_df=recipes_df,
        cost_lookup=cost_lookup,
        bean_change_pct=bean_change_pct,
        dairy_change_pct=dairy_change_pct,
        flavor_change_pct=flavor_change_pct,
        packaging_change_pct=packaging_change_pct,
        sales_multiplier=sales_multiplier,
    )

    total_daily_impact = margin_df["daily_margin_impact"].sum()
    average_margin_drop = (margin_df["projected_margin_pct"] - margin_df["current_margin_pct"]).mean() * 100.0
    highest_risk = margin_df.sort_values("projected_margin_pct").iloc[0]

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Daily Margin Impact", f"${total_daily_impact:,.2f}")
    metric_col2.metric("Average Margin Shift", f"{average_margin_drop:+.2f} pts")
    metric_col3.metric("Most Exposed Drink", highest_risk["item_name"])

    display_df = margin_df[[
        "item_name",
        "menu_price",
        "projected_daily_units",
        "current_cost",
        "projected_cost",
        "current_margin_pct",
        "projected_margin_pct",
        "price_to_hold_margin",
    ]].copy()
    display_df.columns = [
        "Menu Item",
        "Menu Price",
        "Projected Daily Units",
        "Current Cost",
        "Projected Cost",
        "Current Margin %",
        "Projected Margin %",
        "Price to Hold Margin",
    ]

    st.dataframe(display_df, width="stretch", hide_index=True)

    focus_item = st.selectbox("Focus Item", margin_df["item_name"].tolist(), index=0)
    focus_row = margin_df.loc[margin_df["item_name"] == focus_item].iloc[0]

    detail_col1, detail_col2 = st.columns([1.1, 1.3])
    with detail_col1:
        st.markdown("#### Margin Snapshot")
        st.write(f"**Menu price:** ${focus_row['menu_price']:.2f}")
        st.write(f"**Current ingredient cost:** ${focus_row['current_cost']:.2f}")
        st.write(f"**Projected ingredient cost:** ${focus_row['projected_cost']:.2f}")
        st.write(f"**Current margin:** {focus_row['current_margin_pct'] * 100:.1f}%")
        st.write(f"**Projected margin:** {focus_row['projected_margin_pct'] * 100:.1f}%")
        st.write(f"**Suggested new price:** ${focus_row['price_to_hold_margin']:.2f}")

    with detail_col2:
        st.markdown("#### Recommended Action")
        price_gap = float(focus_row["price_to_hold_margin"] - focus_row["menu_price"])
        if price_gap >= 0.35:
            st.error("This drink is carrying a meaningful cost increase. Consider a menu price move or a recipe review.")
        elif price_gap >= 0.15:
            st.warning("Margin compression is noticeable. Watch this item closely over the next buying cycle.")
        else:
            st.success("Projected cost change is manageable without a major menu adjustment.")
        st.caption(
            "This view uses seeded recipe quantities and operational price tables from MySQL, then stress-tests those costs with warehouse-informed scenario inputs."
        )


def render_recipe_and_inventory_views(recipes_df: pd.DataFrame, inventory_df: pd.DataFrame):
    st.markdown("---")
    st.subheader("Operational Tables")
    st.caption("These seeded MySQL tables are the foundation for deeper owner workflows such as supplier management, recipe costing, and reorder logic.")

    view_col1, view_col2 = st.columns(2)
    with view_col1:
        recipe_view = recipes_df[[
            "item_name",
            "ingredient_name",
            "ingredient_category",
            "quantity_per_item",
            "quantity_unit",
            "daily_units",
        ]].copy()
        recipe_view.columns = [
            "Menu Item",
            "Ingredient",
            "Category",
            "Qty per Drink",
            "Unit",
            "Daily Units",
        ]
        st.markdown("#### Recipe Table")
        st.dataframe(recipe_view, width="stretch", hide_index=True)

    with view_col2:
        inventory_view = inventory_df[[
            "ingredient_name",
            "ingredient_category",
            "on_hand_qty",
            "reorder_point_qty",
            "target_qty",
            "quantity_unit",
            "snapshot_date",
        ]].copy()
        inventory_view.columns = [
            "Ingredient",
            "Category",
            "On Hand",
            "Reorder Point",
            "Target Qty",
            "Unit",
            "Snapshot Date",
        ]
        st.markdown("#### Inventory Positions")
        st.dataframe(inventory_view, width="stretch", hide_index=True)


def main():
    inject_owner_theme()
    st.markdown(
        """
        <div class="owner-hero">
            <h1>Owner Planner</h1>
            <div>
                Move from market monitoring to store operations. This page combines warehouse signals from PostgreSQL
                with operational shop data in MySQL so owners can plan purchasing and protect margins.
            </div>
            <div class="owner-chip">Purchasing Planner</div>
            <div class="owner-chip">Supplier Comparison</div>
            <div class="owner-chip">Menu Margin Studio</div>
            <div class="owner-chip">Operational Tables</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        market_df = load_market_data()
        price_df = load_supplier_prices()
        recipes_df = load_menu_recipes()
        inventory_df = load_inventory()
    except Exception as exc:
        st.error("Owner Planner could not load its data sources.")
        st.exception(exc)
        st.stop()

    if market_df.empty:
        st.warning("No warehouse market data was found. Run the ETL pipeline first.")
        st.stop()

    if price_df.empty or recipes_df.empty or inventory_df.empty:
        st.warning("Operational MySQL tables are empty. Reinitialize the MySQL schema to load the Phase 1 seeded data.")
        st.stop()

    render_purchasing_planner(market_df, price_df, recipes_df, inventory_df)
    render_margin_studio(market_df, price_df, recipes_df)
    render_recipe_and_inventory_views(recipes_df, inventory_df)


main()
