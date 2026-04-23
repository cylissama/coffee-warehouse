-- Query 1: Coffee price trend over time
SELECT
    date_id,
    coffee_close,
    coffee_7day_ma,
    coffee_30day_ma
FROM fact_market_features
ORDER BY date_id;

-- Query 2: Compare coffee prices with macroeconomic conditions
SELECT
    date_id,
    coffee_close,
    cpi_value,
    fedfunds_value,
    fertilizer_price_index,
    brl_usd_exchange_rate,
    milk_price_index
FROM fact_market_features
ORDER BY date_id;

-- Query 3: Weather comparison by region
SELECT
    d.date_id,
    r.region_name,
    w.avg_temp,
    w.precipitation
FROM fact_weather_daily w
JOIN dim_date d
    ON w.date_id = d.date_id
JOIN dim_region r
    ON w.region_id = r.region_id
ORDER BY d.date_id, r.region_name;

-- Query 4: Latest decision-support snapshot
SELECT
    f.date_id,
    r.region_name,
    f.coffee_close,
    f.buy_opportunity_score,
    f.buy_signal,
    f.fertilizer_price_index,
    f.brl_usd_exchange_rate,
    f.cpi_value,
    f.fedfunds_value
FROM fact_market_features f
JOIN dim_region r
    ON f.region_id = r.region_id
WHERE f.date_id = (
    SELECT MAX(date_id) FROM fact_market_features
)
ORDER BY r.region_name;

-- Query 5: Monthly average buy score by region
SELECT
    DATE_TRUNC('month', date_id) AS month_start,
    r.region_name,
    AVG(f.buy_opportunity_score) AS avg_buy_score
FROM fact_market_features f
JOIN dim_region r
    ON f.region_id = r.region_id
GROUP BY DATE_TRUNC('month', date_id), r.region_name
ORDER BY month_start, r.region_name;
