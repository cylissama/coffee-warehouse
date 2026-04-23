DROP TABLE IF EXISTS recipes;
DROP TABLE IF EXISTS inventory_positions;
DROP TABLE IF EXISTS supplier_price_history;
DROP TABLE IF EXISTS menu_items;
DROP TABLE IF EXISTS ingredients;
DROP TABLE IF EXISTS suppliers;
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

CREATE TABLE suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(120) NOT NULL,
    origin_region VARCHAR(120),
    lead_time_days INT NOT NULL,
    min_order_lbs DECIMAL(10,2) DEFAULT 0,
    contact_email VARCHAR(150),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE ingredients (
    ingredient_id INT AUTO_INCREMENT PRIMARY KEY,
    ingredient_name VARCHAR(120) NOT NULL,
    ingredient_category VARCHAR(50) NOT NULL,
    purchase_unit VARCHAR(20) NOT NULL,
    is_core BOOLEAN DEFAULT TRUE
);

CREATE TABLE menu_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(120) NOT NULL,
    category VARCHAR(50),
    menu_price DECIMAL(10,2) NOT NULL,
    size_oz DECIMAL(6,2),
    daily_units INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE supplier_price_history (
    price_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    price_date DATE NOT NULL,
    unit_cost DECIMAL(10,4) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    notes VARCHAR(255),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id)
);

CREATE TABLE inventory_positions (
    inventory_id INT AUTO_INCREMENT PRIMARY KEY,
    ingredient_id INT NOT NULL,
    snapshot_date DATE NOT NULL,
    on_hand_qty DECIMAL(12,2) NOT NULL,
    reorder_point_qty DECIMAL(12,2) NOT NULL,
    target_qty DECIMAL(12,2) NOT NULL,
    quantity_unit VARCHAR(20) NOT NULL,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id)
);

CREATE TABLE recipes (
    recipe_id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    quantity_per_item DECIMAL(10,3) NOT NULL,
    quantity_unit VARCHAR(20) NOT NULL,
    FOREIGN KEY (item_id) REFERENCES menu_items(item_id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id)
);

INSERT INTO suppliers (supplier_name, origin_region, lead_time_days, min_order_lbs, contact_email) VALUES
('Summit Bean Imports', 'Brazil', 7, 40.00, 'trade@summitbeans.example'),
('Harbor Coffee Traders', 'Colombia', 10, 60.00, 'orders@harbortraders.example'),
('Metro Dairy Supply', 'Texas', 3, 20.00, 'ops@metrodairy.example'),
('Flavor House', 'Illinois', 5, 10.00, 'sales@flavorhouse.example'),
('Cafe Packaging Co', 'Missouri', 4, 5.00, 'service@cafepackaging.example');

INSERT INTO ingredients (ingredient_name, ingredient_category, purchase_unit, is_core) VALUES
('Espresso Blend Beans', 'beans', 'lb', TRUE),
('Whole Milk', 'dairy', 'fl_oz', TRUE),
('Vanilla Syrup', 'syrup', 'fl_oz', FALSE),
('Chocolate Sauce', 'sauce', 'fl_oz', FALSE),
('Paper Cup', 'packaging', 'each', TRUE),
('Lid', 'packaging', 'each', TRUE);

INSERT INTO menu_items (item_name, category, menu_price, size_oz, daily_units, is_active) VALUES
('Latte', 'Espresso Drinks', 5.75, 12.00, 70, TRUE),
('Cappuccino', 'Espresso Drinks', 5.25, 8.00, 45, TRUE),
('Americano', 'Espresso Drinks', 4.25, 12.00, 38, TRUE),
('Mocha', 'Espresso Drinks', 6.10, 12.00, 32, TRUE),
('Vanilla Latte', 'Espresso Drinks', 6.25, 12.00, 26, TRUE);

INSERT INTO supplier_price_history (supplier_id, ingredient_id, price_date, unit_cost, unit, notes) VALUES
(1, 1, '2026-03-15', 13.1000, 'lb', 'Spring contract quote'),
(1, 1, '2026-04-15', 13.8500, 'lb', 'Current preferred Brazil blend quote'),
(2, 1, '2026-03-15', 13.4500, 'lb', 'Higher minimum order but stable quality'),
(2, 1, '2026-04-15', 14.2000, 'lb', 'Current Colombia blend quote'),
(3, 2, '2026-03-15', 0.0290, 'fl_oz', 'Whole milk distributor quote'),
(3, 2, '2026-04-15', 0.0310, 'fl_oz', 'Current whole milk quote'),
(4, 3, '2026-03-15', 0.1800, 'fl_oz', 'Vanilla syrup bulk case'),
(4, 3, '2026-04-15', 0.2000, 'fl_oz', 'Current vanilla syrup bulk case'),
(4, 4, '2026-03-15', 0.2200, 'fl_oz', 'Chocolate sauce foodservice pack'),
(4, 4, '2026-04-15', 0.2400, 'fl_oz', 'Current chocolate sauce pack'),
(5, 5, '2026-03-15', 0.1350, 'each', 'Cup case cost'),
(5, 5, '2026-04-15', 0.1450, 'each', 'Current cup case cost'),
(5, 6, '2026-03-15', 0.0470, 'each', 'Lid case cost'),
(5, 6, '2026-04-15', 0.0520, 'each', 'Current lid case cost');

INSERT INTO inventory_positions (ingredient_id, snapshot_date, on_hand_qty, reorder_point_qty, target_qty, quantity_unit) VALUES
(1, '2026-04-20', 34.00, 24.00, 72.00, 'lb'),
(2, '2026-04-20', 640.00, 384.00, 1280.00, 'fl_oz'),
(3, '2026-04-20', 96.00, 48.00, 144.00, 'fl_oz'),
(4, '2026-04-20', 120.00, 60.00, 180.00, 'fl_oz'),
(5, '2026-04-20', 320.00, 160.00, 480.00, 'each'),
(6, '2026-04-20', 320.00, 160.00, 480.00, 'each');

INSERT INTO recipes (item_id, ingredient_id, quantity_per_item, quantity_unit) VALUES
(1, 1, 18.000, 'g'),
(1, 2, 10.000, 'fl_oz'),
(1, 5, 1.000, 'each'),
(1, 6, 1.000, 'each'),
(2, 1, 18.000, 'g'),
(2, 2, 6.000, 'fl_oz'),
(2, 5, 1.000, 'each'),
(2, 6, 1.000, 'each'),
(3, 1, 18.000, 'g'),
(3, 5, 1.000, 'each'),
(3, 6, 1.000, 'each'),
(4, 1, 18.000, 'g'),
(4, 2, 9.000, 'fl_oz'),
(4, 4, 1.500, 'fl_oz'),
(4, 5, 1.000, 'each'),
(4, 6, 1.000, 'each'),
(5, 1, 18.000, 'g'),
(5, 2, 10.000, 'fl_oz'),
(5, 3, 1.200, 'fl_oz'),
(5, 5, 1.000, 'each'),
(5, 6, 1.000, 'each');
