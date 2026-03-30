CREATE TABLE IF NOT EXISTS dim_date (
    date_id DATE PRIMARY KEY,
    year INT,
    month INT,
    day INT
);

CREATE TABLE IF NOT EXISTS fact_market_summary (
    date_id DATE PRIMARY KEY,
    coffee_close DECIMAL(10,2),
    avg_temp DECIMAL(6,2),
    precipitation DECIMAL(6,2),
    cpi_value DECIMAL(12,4),
    coffee_7day_ma DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);