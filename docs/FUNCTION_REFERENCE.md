# Function Reference

## ETL Orchestration

| Function | File | Purpose |
| --- | --- | --- |
| `pipeline_start_date` | `etl/run_pipeline.py` | Reads the starting date for historical extraction from environment variables. |
| `mysql_engine` | `etl/run_pipeline.py` | Creates the SQLAlchemy engine for MySQL staging. |
| `postgres_engine` | `etl/run_pipeline.py` | Creates the SQLAlchemy engine for PostgreSQL warehouse access. |
| `log_etl_start` | `etl/run_pipeline.py` | Creates an ETL run log entry in MySQL. |
| `log_etl_finish` | `etl/run_pipeline.py` | Updates ETL run status, row count, and notes. |
| `clear_staging` | `etl/run_pipeline.py` | Empties the MySQL staging tables before reload. |
| `clear_warehouse` | `etl/run_pipeline.py` | Empties the PostgreSQL warehouse tables before reload. |
| `main` | `etl/run_pipeline.py` | Runs extraction, transformation, loading, and logging. |

## Extraction

| Function | File | Purpose |
| --- | --- | --- |
| `fetch_coffee_prices` | `etl/extract/coffee.py` | Downloads historical coffee futures prices from Yahoo Finance. |
| `fetch_weather_data` | `etl/extract/weather.py` | Downloads daily weather observations from Open-Meteo. |
| `fetch_fred_series` | `etl/extract/macro.py` | Downloads macroeconomic indicator observations from FRED. |
| `fetch_article_text` | `etl/extract/news.py` | Scrapes paragraph text from linked article pages. |
| `fetch_coffee_news_rss` | `etl/extract/news.py` | Reads Google News RSS search results and prepares article documents. |

## Transformation and Modeling

| Function | File | Purpose |
| --- | --- | --- |
| `classify_buy_signal` | `etl/transform/build_features.py` | Maps score values to `Buy Now`, `Watch`, `Wait`, or `Insufficient Data`. |
| `train_logistic_regression` | `etl/transform/build_features.py` | Trains a simple logistic regression model with NumPy. |
| `predict_logistic_regression` | `etl/transform/build_features.py` | Generates probabilities from the trained model parameters. |
| `add_buy_opportunity_predictions` | `etl/transform/build_features.py` | Engineers features and appends buy-opportunity scores and labels. |
| `build_dim_date` | `etl/transform/build_features.py` | Creates the warehouse date dimension. |
| `build_dim_region` | `etl/transform/build_features.py` | Creates region dimension records. |
| `build_dim_indicator` | `etl/transform/build_features.py` | Creates macro indicator dimension records. |
| `build_fact_coffee_prices` | `etl/transform/build_features.py` | Builds structured coffee price facts. |
| `build_fact_weather_daily` | `etl/transform/build_features.py` | Builds weather facts by date and region. |
| `build_fact_macro_daily` | `etl/transform/build_features.py` | Builds macroeconomic fact rows by date and indicator. |
| `build_fact_market_features` | `etl/transform/build_features.py` | Produces the integrated analytical feature fact table. |

## MongoDB Loading

| Function | File | Purpose |
| --- | --- | --- |
| `get_mongo_database` | `etl/load/load_mongo.py` | Connects to MongoDB and returns the configured database. |
| `reset_mongo_collections` | `etl/load/load_mongo.py` | Clears raw document collections. |
| `load_coffee_documents` | `etl/load/load_mongo.py` | Loads coffee raw records into MongoDB. |
| `load_weather_documents` | `etl/load/load_mongo.py` | Loads weather raw records into MongoDB. |
| `load_macro_documents` | `etl/load/load_mongo.py` | Loads macro raw records into MongoDB. |
| `load_news_documents` | `etl/load/load_mongo.py` | Loads scraped news documents into MongoDB. |
| `reset_news_collection` | `etl/load/load_mongo.py` | Clears the news article collection. |

## Dashboard Application

### Core data and state functions

| Function | File | Purpose |
| --- | --- | --- |
| `inject_theme` | `dashboard/Home.py` | Applies custom dashboard styling. |
| `get_engine` | `dashboard/Home.py` | Connects the dashboard to PostgreSQL. |
| `load_warehouse_data` | `dashboard/Home.py` | Queries warehouse data for dashboard use. |
| `initialize_dashboard_state` | `dashboard/Home.py` | Creates initial Streamlit session-state defaults. |
| `apply_template` | `dashboard/Home.py` | Loads preset dashboard views. |
| `apply_template_to_state` | `dashboard/Home.py` | Pushes template defaults into session state. |
| `filter_dataframe` | `dashboard/Home.py` | Filters records by date range. |
| `prepare_region_scope` | `dashboard/Home.py` | Aggregates or isolates selected regional views. |
| `aggregate_dataframe` | `dashboard/Home.py` | Aggregates metrics by daily, weekly, or monthly grain. |

### Dashboard analytics helpers

| Function | File | Purpose |
| --- | --- | --- |
| `safe_period_change` | `dashboard/Home.py` | Computes percent changes over a lookback window safely. |
| `safe_period_diff` | `dashboard/Home.py` | Computes absolute differences over a lookback window safely. |
| `compute_cost_pressure_summary` | `dashboard/Home.py` | Summarizes macro and input-cost pressure levels. |
| `compute_price_review_alert` | `dashboard/Home.py` | Converts warehouse signals into menu pricing alerts. |
| `compute_buy_score_drivers` | `dashboard/Home.py` | Builds explanatory signal buckets behind the buy score. |
| `build_buy_opportunity_context` | `dashboard/Home.py` | Generates narrative explanation for the current buy score. |

### Dashboard rendering functions

| Function | File | Purpose |
| --- | --- | --- |
| `render_chart` | `dashboard/Home.py` | Renders charts from aggregated data. |
| `render_visual_snapshot` | `dashboard/Home.py` | Shows quick-read visual summaries. |
| `render_buy_score_driver_panel` | `dashboard/Home.py` | Displays directional drivers behind the buy score. |
| `render_owner_action_center` | `dashboard/Home.py` | Shows purchasing, pricing, and pressure recommendations. |
| `render_margin_impact_calculator` | `dashboard/Home.py` | Estimates drink-margin effects from bean cost changes. |
| `render_buy_opportunity_score` | `dashboard/Home.py` | Displays the current score and interpretation. |
| `render_kpis` | `dashboard/Home.py` | Displays key business and market metrics. |
| `render_overview_charts` | `dashboard/Home.py` | Shows trend charts for key market inputs. |
| `main` | `dashboard/Home.py` | Runs the full Streamlit dashboard page. |

## Supporting Streamlit Pages

| Component | File | Purpose |
| --- | --- | --- |
| Information page | `dashboard/pages/1_Information.py` | Explains metrics, sources, and ETL flow. |
| News page | `dashboard/pages/2_News.py` | Provides MongoDB-backed article search and display. |
