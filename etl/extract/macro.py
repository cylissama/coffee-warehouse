import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def fetch_fred_series(series_id: str, start="2024-01-01", end="2025-12-31") -> pd.DataFrame:
    """
    Fetch a FRED time series by series ID.
    Example:
      CPIAUCSL = Consumer Price Index for All Urban Consumers
      FEDFUNDS = Effective Federal Funds Rate
    """
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise ValueError("FRED_API_KEY not found in environment.")

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start,
        "observation_end": end,
    }

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    payload = response.json()

    observations = payload.get("observations", [])
    if not observations:
        raise ValueError(f"No FRED observations returned for {series_id}.")

    df = pd.DataFrame(observations)[["date", "value"]].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])

    df = df.rename(columns={
        "date": "macro_date",
        "value": "indicator_value"
    })
    df["indicator_name"] = series_id
    df["source"] = "fred"

    return df