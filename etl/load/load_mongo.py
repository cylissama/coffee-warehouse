import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


def get_mongo_database():
    host = os.getenv("MONGO_HOST", "localhost")
    port = int(os.getenv("MONGO_PORT", "27017"))
    db_name = os.getenv("MONGO_DB", "coffee_intelligence")

    client = MongoClient(host=host, port=port)
    return client[db_name]


def reset_mongo_collections(db):
    db.raw_coffee_documents.delete_many({})
    db.raw_weather_documents.delete_many({})
    db.raw_macro_documents.delete_many({})


def load_coffee_documents(db, coffee_df):
    records = []
    for _, row in coffee_df.iterrows():
        records.append({
            "source_type": "market_data",
            "dataset": "coffee_futures",
            "source": row.get("source"),
            "trade_date": str(row.get("trade_date")),
            "open_price": None if row.get("open_price") is None else float(row.get("open_price")),
            "high_price": None if row.get("high_price") is None else float(row.get("high_price")),
            "low_price": None if row.get("low_price") is None else float(row.get("low_price")),
            "close_price": None if row.get("close_price") is None else float(row.get("close_price")),
            "volume": None if row.get("volume") is None else int(row.get("volume")),
            "document_kind": "raw_market_record"
        })

    if records:
        db.raw_coffee_documents.insert_many(records)


def load_weather_documents(db, weather_df):
    records = []
    for _, row in weather_df.iterrows():
        records.append({
            "source_type": "weather_data",
            "dataset": "historical_weather",
            "source": row.get("source"),
            "weather_date": str(row.get("weather_date")),
            "location_name": row.get("location_name"),
            "latitude": None if row.get("latitude") is None else float(row.get("latitude")),
            "longitude": None if row.get("longitude") is None else float(row.get("longitude")),
            "avg_temp": None if row.get("avg_temp") is None else float(row.get("avg_temp")),
            "precipitation": None if row.get("precipitation") is None else float(row.get("precipitation")),
            "document_kind": "raw_weather_record"
        })

    if records:
        db.raw_weather_documents.insert_many(records)


def load_macro_documents(db, macro_df):
    records = []
    for _, row in macro_df.iterrows():
        records.append({
            "source_type": "macro_data",
            "dataset": "fred_series",
            "source": row.get("source"),
            "macro_date": str(row.get("macro_date")),
            "indicator_name": row.get("indicator_name"),
            "indicator_value": None if row.get("indicator_value") is None else float(row.get("indicator_value")),
            "document_kind": "raw_macro_record"
        })

    if records:
        db.raw_macro_documents.insert_many(records)
    
def load_news_documents(db, articles: list[dict]):
    if articles:
        db.coffee_news_articles.insert_many(articles)


def reset_news_collection(db):
    db.coffee_news_articles.delete_many({})