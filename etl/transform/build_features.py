import numpy as np
import pandas as pd


BUY_SCORE_FEATURES = [
    "coffee_daily_return",
    "price_vs_7day_ma",
    "price_vs_30day_ma",
    "coffee_30day_volatility",
    "temp_7day_avg",
    "precip_7day_avg",
    "precip_30day_avg",
    "fertilizer_30day_change",
    "cpi_30day_change",
    "fedfunds_30day_change",
]


def classify_buy_signal(score: float) -> str:
    if pd.isna(score):
        return "Insufficient Data"
    if score >= 60:
        return "Buy Now"
    if score >= 45:
        return "Watch"
    return "Wait"


def train_logistic_regression(feature_df: pd.DataFrame, target: pd.Series):
    features = feature_df.to_numpy(dtype=float)
    labels = target.to_numpy(dtype=float)

    means = features.mean(axis=0)
    stds = features.std(axis=0)
    stds[stds == 0] = 1.0

    scaled_features = (features - means) / stds
    weights = np.zeros(scaled_features.shape[1], dtype=float)
    bias = 0.0

    learning_rate = 0.05
    regularization = 0.01
    num_rows = len(labels)

    for _ in range(600):
        linear_response = np.clip((scaled_features @ weights) + bias, -30, 30)
        probabilities = 1.0 / (1.0 + np.exp(-linear_response))
        errors = probabilities - labels

        weight_gradient = (scaled_features.T @ errors) / num_rows
        weight_gradient += regularization * weights
        bias_gradient = errors.mean()

        weights -= learning_rate * weight_gradient
        bias -= learning_rate * bias_gradient

    return means, stds, weights, bias


def predict_logistic_regression(feature_df: pd.DataFrame, model_params) -> np.ndarray:
    means, stds, weights, bias = model_params
    features = feature_df.to_numpy(dtype=float)
    scaled_features = (features - means) / stds
    linear_response = np.clip((scaled_features @ weights) + bias, -30, 30)
    return 1.0 / (1.0 + np.exp(-linear_response))


def add_buy_opportunity_predictions(df: pd.DataFrame) -> pd.DataFrame:
    working_df = df.copy().sort_values("trade_date").reset_index(drop=True)

    working_df["price_vs_7day_ma"] = (
        (working_df["close_price"] - working_df["coffee_7day_ma"]) / working_df["coffee_7day_ma"]
    )
    working_df["price_vs_30day_ma"] = (
        (working_df["close_price"] - working_df["coffee_30day_ma"]) / working_df["coffee_30day_ma"]
    )
    working_df["temp_7day_avg"] = working_df["avg_temp"].rolling(7, min_periods=7).mean()
    working_df["precip_7day_avg"] = working_df["precipitation"].rolling(7, min_periods=7).mean()
    working_df["precip_30day_avg"] = working_df["precipitation"].rolling(30, min_periods=30).mean()
    working_df["fertilizer_30day_change"] = working_df["fertilizer_price_index"].pct_change(30)
    working_df["cpi_30day_change"] = working_df["cpi_value"].pct_change(30)
    working_df["fedfunds_30day_change"] = working_df["fedfunds_value"].diff(30)
    working_df["future_7d_return"] = (
        working_df["close_price"].shift(-7) / working_df["close_price"]
    ) - 1
    working_df["target_price_up_7d"] = pd.Series(pd.NA, index=working_df.index, dtype="Int64")
    future_mask = working_df["future_7d_return"].notna()
    working_df.loc[future_mask, "target_price_up_7d"] = (
        working_df.loc[future_mask, "future_7d_return"] > 0
    ).astype(int)

    feature_frame = working_df[BUY_SCORE_FEATURES].replace([float("inf"), -float("inf")], float("nan"))
    training_df = feature_frame.copy()
    training_df["target_price_up_7d"] = working_df["target_price_up_7d"]
    training_df = training_df.dropna()

    working_df["buy_opportunity_score"] = float("nan")

    if len(training_df) >= 60 and training_df["target_price_up_7d"].nunique() >= 2:
        model_params = train_logistic_regression(
            training_df[BUY_SCORE_FEATURES],
            training_df["target_price_up_7d"].astype(int),
        )

        scorable_mask = feature_frame.notna().all(axis=1)
        if scorable_mask.any():
            probabilities = predict_logistic_regression(
                feature_frame.loc[scorable_mask, BUY_SCORE_FEATURES],
                model_params,
            )
            working_df.loc[scorable_mask, "buy_opportunity_score"] = probabilities * 100.0

    working_df["buy_opportunity_score"] = working_df["buy_opportunity_score"].round(2)
    working_df["buy_signal"] = working_df["buy_opportunity_score"].apply(classify_buy_signal)

    return working_df


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
        },
        {
            "indicator_name": "PCU3253132531",
            "description": "Producer Price Index by Industry: Fertilizer Manufacturing",
            "unit": "index",
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
    fertilizer: pd.DataFrame,
    region_id: int
) -> pd.DataFrame:
    coffee = coffee.copy()
    weather = weather.copy()
    cpi = cpi.copy()
    fedfunds = fedfunds.copy()
    fertilizer = fertilizer.copy()

    coffee["trade_date"] = pd.to_datetime(coffee["trade_date"])
    weather["weather_date"] = pd.to_datetime(weather["weather_date"])
    cpi["macro_date"] = pd.to_datetime(cpi["macro_date"])
    fedfunds["macro_date"] = pd.to_datetime(fedfunds["macro_date"])
    fertilizer["macro_date"] = pd.to_datetime(fertilizer["macro_date"])

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
    df = df.merge(
        fertilizer[["macro_date", "indicator_value"]].rename(columns={"indicator_value": "fertilizer_price_index"}),
        left_on="trade_date",
        right_on="macro_date",
        how="left"
    )

    df = df.sort_values("trade_date")
    df["cpi_value"] = df["cpi_value"].ffill()
    df["fedfunds_value"] = df["fedfunds_value"].ffill()
    df["fertilizer_price_index"] = df["fertilizer_price_index"].ffill()

    df["coffee_daily_return"] = df["close_price"].pct_change()
    df["coffee_7day_ma"] = df["close_price"].rolling(7, min_periods=1).mean()
    df["coffee_30day_ma"] = df["close_price"].rolling(30, min_periods=1).mean()
    df["coffee_30day_volatility"] = df["coffee_daily_return"].rolling(30, min_periods=2).std()
    df = add_buy_opportunity_predictions(df)

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
        "fedfunds_value": df["fedfunds_value"],
        "fertilizer_price_index": df["fertilizer_price_index"],
        "buy_opportunity_score": df["buy_opportunity_score"],
        "buy_signal": df["buy_signal"],
    }).drop_duplicates(subset=["date_id", "region_id"])
