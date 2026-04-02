import pandas as pd


def build_dim_date(dates: pd.Series) -> pd.DataFrame:
    df = pd.DataFrame({"date_id": pd.to_datetime(dates).dt.date}).drop_duplicates()
    dt = pd.to_datetime(df["date_id"])

    df["year"] = dt.dt.year
    df["month"] = dt.dt.month
    df["day"] = dt.dt.day
    df["quarter"] = dt.dt.quarter
    df["month_name"] = dt.dt.month_name()
    df["day_of_week"] = dt.dt.day_name()

    return df.sort_values("date_id").reset_index(drop=True)


def build_dim_region(region_name: str, country: str, latitude: float, longitude: float) -> pd.DataFrame:
    return pd.DataFrame([{
        "region_name": region_name,
        "country": country,
        "latitude": latitude,
        "longitude": longitude
    }])


def build_dim_indicator() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "indicator_name": "CPIAUCSL",
            "description": "Consumer Price Index for All Urban Consumers",
            "unit": "index",
            "source": "fred"
        },
        {
            "indicator_name": "FEDFUNDS",
            "description": "Effective Federal Funds Rate",
            "unit": "percent",
            "source": "fred"
        }
    ])


def build_fact_coffee_prices(coffee: pd.DataFrame) -> pd.DataFrame:
    df = coffee.copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date

    return pd.DataFrame({
        "date_id": df["trade_date"],
        "open_price": df.get("open_price"),
        "high_price": df.get("high_price"),
        "low_price": df.get("low_price"),
        "close_price": df.get("close_price"),
        "volume": df.get("volume"),
        "source": df.get("source")
    })


def build_fact_weather_daily(weather: pd.DataFrame, region_id: int) -> pd.DataFrame:
    df = weather.copy()
    df["weather_date"] = pd.to_datetime(df["weather_date"]).dt.date

    return pd.DataFrame({
        "date_id": df["weather_date"],
        "region_id": region_id,
        "avg_temp": df["avg_temp"],
        "precipitation": df["precipitation"],
        "source": df["source"]
    })


def build_fact_macro_daily(macro: pd.DataFrame, indicator_lookup: dict) -> pd.DataFrame:
    df = macro.copy()
    df["macro_date"] = pd.to_datetime(df["macro_date"]).dt.date
    df["indicator_id"] = df["indicator_name"].map(indicator_lookup)

    return pd.DataFrame({
        "date_id": df["macro_date"],
        "indicator_id": df["indicator_id"],
        "indicator_value": df["indicator_value"],
        "source": df["source"]
    })


def build_fact_market_features(
    coffee: pd.DataFrame,
    weather: pd.DataFrame,
    cpi: pd.DataFrame,
    fedfunds: pd.DataFrame,
    region_id: int
) -> pd.DataFrame:
    coffee = coffee.copy()
    weather = weather.copy()
    cpi = cpi.copy()
    fedfunds = fedfunds.copy()

    coffee["trade_date"] = pd.to_datetime(coffee["trade_date"])
    weather["weather_date"] = pd.to_datetime(weather["weather_date"])
    cpi["macro_date"] = pd.to_datetime(cpi["macro_date"])
    fedfunds["macro_date"] = pd.to_datetime(fedfunds["macro_date"])

    df = coffee.merge(weather, left_on="trade_date", right_on="weather_date", how="left")
    df = df.merge(
        cpi[["macro_date", "indicator_value"]].rename(columns={"indicator_value": "cpi_value"}),
        left_on="trade_date",
        right_on="macro_date",
        how="left"
    )
    df = df.merge(
        fedfunds[["macro_date", "indicator_value"]].rename(columns={"indicator_value": "fedfunds_value"}),
        left_on="trade_date",
        right_on="macro_date",
        how="left"
    )

    df = df.sort_values("trade_date")
    df["cpi_value"] = df["cpi_value"].ffill()
    df["fedfunds_value"] = df["fedfunds_value"].ffill()

    df["coffee_daily_return"] = df["close_price"].pct_change()
    df["coffee_7day_ma"] = df["close_price"].rolling(7, min_periods=1).mean()
    df["coffee_30day_ma"] = df["close_price"].rolling(30, min_periods=1).mean()
    df["coffee_30day_volatility"] = df["coffee_daily_return"].rolling(30, min_periods=2).std()

    return pd.DataFrame({
        "date_id": df["trade_date"].dt.date,
        "region_id": region_id,
        "coffee_close": df["close_price"],
        "coffee_daily_return": df["coffee_daily_return"],
        "coffee_7day_ma": df["coffee_7day_ma"],
        "coffee_30day_ma": df["coffee_30day_ma"],
        "coffee_30day_volatility": df["coffee_30day_volatility"],
        "avg_temp": df["avg_temp"],
        "precipitation": df["precipitation"],
        "cpi_value": df["cpi_value"],
        "fedfunds_value": df["fedfunds_value"]
    }).drop_duplicates(subset=["date_id", "region_id"])