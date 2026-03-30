import yfinance as yf
import pandas as pd


def fetch_coffee_prices(start="2024-01-01", end="2025-12-31") -> pd.DataFrame:
    """
    Fetch historical coffee futures data from Yahoo Finance via yfinance.
    Ticker: KC=F
    """
    df = yf.download("KC=F", start=start, end=end, auto_adjust=False, progress=False)

    if df.empty:
        raise ValueError("No coffee price data returned from Yahoo Finance.")

    df = df.reset_index()

    # Handle both normal and multi-index columns safely
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

    df = df.rename(columns={
        "Date": "trade_date",
        "Close": "close_price",
        "Open": "open_price",
        "High": "high_price",
        "Low": "low_price",
        "Volume": "volume"
    })

    keep_cols = [c for c in ["trade_date", "open_price", "high_price", "low_price", "close_price", "volume"] if c in df.columns]
    df = df[keep_cols].copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df["source"] = "yfinance_KC=F"

    return df