DROP TABLE IF EXISTS fact_market_features;
DROP TABLE IF EXISTS fact_macro_daily;
DROP TABLE IF EXISTS fact_weather_daily;
DROP TABLE IF EXISTS fact_coffee_prices;
DROP TABLE IF EXISTS dim_indicator;
DROP TABLE IF EXISTS dim_region;
DROP TABLE IF EXISTS dim_date;

CREATE TABLE dim_date (
    date_id DATE PRIMARY KEY,
    year INT NOT NULL,
    month INT NOT NULL,
    day INT NOT NULL,
    quarter INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day_of_week VARCHAR(20) NOT NULL
);

CREATE TABLE dim_region (
    region_id SERIAL PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL UNIQUE,
    country VARCHAR(100),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6)
);

CREATE TABLE dim_indicator (
    indicator_id SERIAL PRIMARY KEY,
    indicator_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    unit VARCHAR(50),
    source VARCHAR(100)
);

CREATE TABLE fact_coffee_prices (
    coffee_price_id SERIAL PRIMARY KEY,
    date_id DATE NOT NULL REFERENCES dim_date(date_id),
    open_price DECIMAL(12,4),
    high_price DECIMAL(12,4),
    low_price DECIMAL(12,4),
    close_price DECIMAL(12,4),
    volume BIGINT,
    source VARCHAR(100)
);

CREATE TABLE fact_weather_daily (
    weather_id SERIAL PRIMARY KEY,
    date_id DATE NOT NULL REFERENCES dim_date(date_id),
    region_id INT NOT NULL REFERENCES dim_region(region_id),
    avg_temp DECIMAL(8,4),
    precipitation DECIMAL(8,4),
    source VARCHAR(100)
);

CREATE TABLE fact_macro_daily (
    macro_id SERIAL PRIMARY KEY,
    date_id DATE NOT NULL REFERENCES dim_date(date_id),
    indicator_id INT NOT NULL REFERENCES dim_indicator(indicator_id),
    indicator_value DECIMAL(14,6),
    source VARCHAR(100)
);

CREATE TABLE fact_market_features (
    feature_id SERIAL PRIMARY KEY,
    date_id DATE NOT NULL REFERENCES dim_date(date_id),
    region_id INT NOT NULL REFERENCES dim_region(region_id),

    coffee_close DECIMAL(12,4),
    coffee_daily_return DECIMAL(12,6),
    coffee_7day_ma DECIMAL(12,4),
    coffee_30day_ma DECIMAL(12,4),
    coffee_30day_volatility DECIMAL(12,6),

    avg_temp DECIMAL(8,4),
    precipitation DECIMAL(8,4),

    cpi_value DECIMAL(14,6),
    fedfunds_value DECIMAL(14,6),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(date_id, region_id)
);