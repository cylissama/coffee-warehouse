import requests
import pandas as pd


def fetch_weather_data(
    latitude=-23.55,
    longitude=-46.63,
    start="2024-01-01",
    end="2025-12-31"
) -> pd.DataFrame:
    """
    Fetch historical daily weather from Open-Meteo.
    Default coordinates: Sao Paulo, Brazil
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start,
        "end_date": end,
        "daily": [
            "temperature_2m_mean",
            "precipitation_sum"
        ],
        "timezone": "auto"
    }

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()

    daily = data.get("daily")
    if not daily:
        raise ValueError("No weather data returned from Open-Meteo.")

    df = pd.DataFrame({
        "weather_date": pd.to_datetime(daily["time"]).date,
        "avg_temp": daily["temperature_2m_mean"],
        "precipitation": daily["precipitation_sum"],
    })

    df["location_name"] = "Sao Paulo, Brazil"
    df["latitude"] = latitude
    df["longitude"] = longitude
    df["source"] = "open-meteo"

    return df