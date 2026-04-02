CREATE TABLE IF NOT EXISTS raw_coffee_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trade_date DATE,
    close_price DECIMAL(10,2),
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw_weather_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    weather_date DATE,
    avg_temp DECIMAL(6,2),
    precipitation DECIMAL(6,2),
    location_name VARCHAR(100),
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw_macro_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    macro_date DATE,
    indicator_name VARCHAR(100),
    indicator_value DECIMAL(12,4),
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);