import os
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from etl.extract.coffee import fetch_coffee_prices
from etl.extract.weather import fetch_weather_data
from etl.extract.macro import fetch_fred_series
from etl.transform.build_features import (
    build_dim_date,
    build_dim_region,
    build_dim_indicator,
    build_fact_coffee_prices,
    build_fact_weather_daily,
    build_fact_macro_daily,
    build_fact_market_features,
)

from etl.extract.news import fetch_coffee_news_rss
from etl.load.load_mongo import (
    get_mongo_database,
    reset_mongo_collections,
    load_coffee_documents,
    load_weather_documents,
    load_macro_documents,
    load_news_documents,
    reset_news_collection,
)

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


def log_etl_start(mysql_eng, job_name: str) -> int:
    started_at = datetime.now()
    with mysql_eng.begin() as conn:
        result = conn.execute(
            text("""
                INSERT INTO etl_job_runs (job_name, run_status, started_at, rows_loaded, notes)
                VALUES (:job_name, :run_status, :started_at, :rows_loaded, :notes)
            """),
            {
                "job_name": job_name,
                "run_status": "RUNNING",
                "started_at": started_at,
                "rows_loaded": 0,
                "notes": "ETL job started"
            }
        )
        return result.lastrowid


def log_etl_finish(mysql_eng, run_id: int, status: str, rows_loaded: int, notes: str):
    ended_at = datetime.now()
    with mysql_eng.begin() as conn:
        conn.execute(
            text("""
                UPDATE etl_job_runs
                SET run_status = :run_status,
                    ended_at = :ended_at,
                    rows_loaded = :rows_loaded,
                    notes = :notes
                WHERE id = :id
            """),
            {
                "run_status": status,
                "ended_at": ended_at,
                "rows_loaded": rows_loaded,
                "notes": notes,
                "id": run_id
            }
        )


def clear_staging(mysql_eng):
    with mysql_eng.begin() as conn:
        conn.execute(text("DELETE FROM raw_coffee_prices"))
        conn.execute(text("DELETE FROM raw_weather_data"))
        conn.execute(text("DELETE FROM raw_macro_data"))


def clear_warehouse(pg_eng):
    with pg_eng.begin() as conn:
        conn.execute(text("DELETE FROM fact_market_features"))
        conn.execute(text("DELETE FROM fact_macro_daily"))
        conn.execute(text("DELETE FROM fact_weather_daily"))
        conn.execute(text("DELETE FROM fact_coffee_prices"))
        conn.execute(text("DELETE FROM dim_indicator"))
        conn.execute(text("DELETE FROM dim_region"))
        conn.execute(text("DELETE FROM dim_date"))


def main():
    mysql_eng = mysql_engine()
    pg_eng = postgres_engine()
    mongo_db = get_mongo_database()
    end_date = datetime.now().strftime("%Y-%m-%d")

    run_id = log_etl_start(mysql_eng, "coffee_market_pipeline")

    try:
        print("Extracting source data...")
        coffee = fetch_coffee_prices(start="2024-01-01", end=end_date)
        weather = fetch_weather_data(start="2024-01-01", end=end_date)
        cpi = fetch_fred_series("CPIAUCSL", start="2024-01-01", end=end_date)
        fedfunds = fetch_fred_series("FEDFUNDS", start="2024-01-01", end=end_date)
        fertilizer = fetch_fred_series("PCU3253132531", start="2024-01-01", end=end_date)
        print("Extracting coffee news articles...")
        news_articles = fetch_coffee_news_rss(max_articles=20)

        macro = pd.concat([cpi, fedfunds, fertilizer], ignore_index=True)

        print("Clearing staging and warehouse tables...")
        clear_staging(mysql_eng)
        clear_warehouse(pg_eng)

        print("Clearing MongoDB collections...")
        reset_mongo_collections(mongo_db)
        reset_news_collection(mongo_db)
        
        print("Loading staging tables...")
        coffee.to_sql("raw_coffee_prices", mysql_eng, if_exists="append", index=False)
        weather.to_sql("raw_weather_data", mysql_eng, if_exists="append", index=False)
        macro.to_sql("raw_macro_data", mysql_eng, if_exists="append", index=False)

        print("Loading MongoDB documents...")
        load_coffee_documents(mongo_db, coffee)
        load_weather_documents(mongo_db, weather)
        load_macro_documents(mongo_db, macro)
        load_news_documents(mongo_db, news_articles)

        print("Building dimensions...")
        all_dates = pd.concat([
            pd.to_datetime(coffee["trade_date"]),
            pd.to_datetime(weather["weather_date"]),
            pd.to_datetime(macro["macro_date"])
        ], ignore_index=True)

        dim_date = build_dim_date(all_dates)
        dim_region = build_dim_region(
            region_name="Sao Paulo, Brazil",
            country="Brazil",
            latitude=-23.55,
            longitude=-46.63
        )
        dim_indicator = build_dim_indicator()

        print("Loading dimensions...")
        dim_date.to_sql("dim_date", pg_eng, if_exists="append", index=False)
        dim_region.to_sql("dim_region", pg_eng, if_exists="append", index=False)
        dim_indicator.to_sql("dim_indicator", pg_eng, if_exists="append", index=False)

        region_lookup = pd.read_sql("SELECT region_id, region_name FROM dim_region", pg_eng)
        indicator_lookup_df = pd.read_sql("SELECT indicator_id, indicator_name FROM dim_indicator", pg_eng)

        region_id = int(region_lookup.loc[region_lookup["region_name"] == "Sao Paulo, Brazil", "region_id"].iloc[0])
        indicator_lookup = dict(zip(indicator_lookup_df["indicator_name"], indicator_lookup_df["indicator_id"]))

        print("Building fact tables...")
        fact_coffee = build_fact_coffee_prices(coffee)
        fact_weather = build_fact_weather_daily(weather, region_id)
        fact_macro = build_fact_macro_daily(macro, indicator_lookup)
        fact_features = build_fact_market_features(coffee, weather, cpi, fedfunds, fertilizer, region_id)

        print("Loading fact tables...")
        fact_coffee.to_sql("fact_coffee_prices", pg_eng, if_exists="append", index=False)
        fact_weather.to_sql("fact_weather_daily", pg_eng, if_exists="append", index=False)
        fact_macro.to_sql("fact_macro_daily", pg_eng, if_exists="append", index=False)
        fact_features.to_sql("fact_market_features", pg_eng, if_exists="append", index=False)

        rows_loaded = len(fact_features)
        log_etl_finish(mysql_eng, run_id, "SUCCESS", rows_loaded, "Pipeline completed successfully")
        print("Pipeline completed successfully.")

    except Exception as e:
        log_etl_finish(mysql_eng, run_id, "FAILED", 0, str(e))
        raise


if __name__ == "__main__":
    main()
