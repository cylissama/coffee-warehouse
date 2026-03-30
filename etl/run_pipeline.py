import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text

from extract.coffee import fetch_coffee_prices
from extract.weather import fetch_weather_data
from extract.macro import fetch_fred_series

load_dotenv()


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


def clear_staging(mysql_eng):
    with mysql_eng.begin() as conn:
        conn.execute(text("DELETE FROM raw_coffee_prices"))
        conn.execute(text("DELETE FROM raw_weather_data"))
        conn.execute(text("DELETE FROM raw_macro_data"))


def clear_warehouse(pg_eng):
    with pg_eng.begin() as conn:
        conn.execute(text("DELETE FROM fact_market_summary"))
        conn.execute(text("DELETE FROM dim_date"))


def load_staging(mysql_eng, coffee, weather, macro):
    coffee.to_sql("raw_coffee_prices", mysql_eng, if_exists="append", index=False)
    weather.to_sql("raw_weather_data", mysql_eng, if_exists="append", index=False)
    macro.to_sql("raw_macro_data", mysql_eng, if_exists="append", index=False)


def transform_for_warehouse(coffee, weather, macro):
    coffee["trade_date"] = pd.to_datetime(coffee["trade_date"])
    weather["weather_date"] = pd.to_datetime(weather["weather_date"])
    macro["macro_date"] = pd.to_datetime(macro["macro_date"])

    # Use CPIAUCSL first
    cpi = macro[macro["indicator_name"] == "CPIAUCSL"].copy()

    df = coffee.merge(
        weather,
        left_on="trade_date",
        right_on="weather_date",
        how="left"
    )

    df = df.merge(
        cpi,
        left_on="trade_date",
        right_on="macro_date",
        how="left"
    )

    # Forward fill CPI because it is monthly while coffee is daily
    df = df.sort_values("trade_date")
    df["indicator_value"] = df["indicator_value"].ffill()

    fact = pd.DataFrame({
        "date_id": df["trade_date"].dt.date,
        "coffee_close": df["close_price"],
        "avg_temp": df["avg_temp"],
        "precipitation": df["precipitation"],
        "cpi_value": df["indicator_value"]
    })

    fact["coffee_7day_ma"] = fact["coffee_close"].rolling(7, min_periods=1).mean()

    dim_date = pd.DataFrame({"date_id": pd.to_datetime(fact["date_id"])})
    dim_date["year"] = dim_date["date_id"].dt.year
    dim_date["month"] = dim_date["date_id"].dt.month
    dim_date["day"] = dim_date["date_id"].dt.day
    dim_date["date_id"] = dim_date["date_id"].dt.date

    return dim_date.drop_duplicates(), fact.drop_duplicates(subset=["date_id"])


def load_warehouse(pg_eng, dim_date, fact):
    dim_date.to_sql("dim_date", pg_eng, if_exists="append", index=False)
    fact.to_sql("fact_market_summary", pg_eng, if_exists="append", index=False)


def main():
    mysql_eng = mysql_engine()
    pg_eng = postgres_engine()

    print("Extracting real data...")
    coffee = fetch_coffee_prices(start="2024-01-01", end="2025-12-31")
    weather = fetch_weather_data(start="2024-01-01", end="2025-12-31")
    macro = fetch_fred_series("CPIAUCSL", start="2024-01-01", end="2025-12-31")

    print("Clearing old data...")
    clear_staging(mysql_eng)
    clear_warehouse(pg_eng)

    print("Loading staging...")
    load_staging(mysql_eng, coffee, weather, macro)

    print("Transforming...")
    dim_date, fact = transform_for_warehouse(coffee, weather, macro)

    print("Loading warehouse...")
    load_warehouse(pg_eng, dim_date, fact)

    print("Pipeline completed successfully with real data.")


if __name__ == "__main__":
    main()