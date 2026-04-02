DROP TABLE IF EXISTS etl_job_runs;
DROP TABLE IF EXISTS raw_macro_data;
DROP TABLE IF EXISTS raw_weather_data;
DROP TABLE IF EXISTS raw_coffee_prices;

CREATE TABLE raw_coffee_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trade_date DATE,
    open_price DECIMAL(12,4),
    high_price DECIMAL(12,4),
    low_price DECIMAL(12,4),
    close_price DECIMAL(12,4),
    volume BIGINT,
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE raw_weather_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    weather_date DATE,
    avg_temp DECIMAL(8,4),
    precipitation DECIMAL(8,4),
    location_name VARCHAR(100),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE raw_macro_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    macro_date DATE,
    indicator_name VARCHAR(100),
    indicator_value DECIMAL(14,6),
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE etl_job_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_name VARCHAR(100),
    run_status VARCHAR(20),
    started_at DATETIME,
    ended_at DATETIME,
    rows_loaded INT,
    notes TEXT
);