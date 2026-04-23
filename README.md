# Coffee Market Intelligence Warehouse

This project implements a multi-database financial market intelligence warehouse focused on coffee market analysis. It collects commodity, macroeconomic, weather, and news data; transforms the data into analytical features; stores it across MySQL, PostgreSQL, and MongoDB; and presents decision-support outputs through a Streamlit dashboard.

## Project Objectives

- Build a hybrid data platform using multiple database systems.
- Implement ETL pipelines for heterogeneous market data sources.
- Support analytical queries on coffee prices, weather, and macro drivers.
- Provide decision-support views for purchasing and pricing decisions.

## Repository Structure

- `etl/`: extraction, transformation, and pipeline orchestration code
- `sql/mysql/`: MySQL staging schema
- `sql/postgres/`: PostgreSQL warehouse schema
- `dashboard/`: Streamlit dashboard application
- `docs/`: project report, requirements audit, and supporting documentation
- `data/`: placeholders for raw and processed exports
- `docker-compose.yml`: local database stack for MySQL, PostgreSQL, and MongoDB

## Technology Stack

- Python
- Pandas, NumPy, SQLAlchemy
- Streamlit and Plotly
- MySQL 8
- PostgreSQL 15
- MongoDB 7
- Docker Compose
- Yahoo Finance via `yfinance`
- FRED API
- Open-Meteo API
- Google News RSS with BeautifulSoup-based scraping

## Architecture Summary

- MySQL stores raw staging data and ETL run logs.
- PostgreSQL stores warehouse dimensions and fact tables for analytics.
- MongoDB stores semi-structured raw documents and scraped news articles.
- Streamlit reads PostgreSQL for analytics and MongoDB for the news view.

See `docs/PROJECT_REPORT.md` for the full architecture diagram and design discussion.

## Data Sources

- Coffee futures: Yahoo Finance ticker `KC=F`
- Weather: Open-Meteo archive API for Sao Paulo, Belo Horizonte, and Vitoria
- Macroeconomic indicators from FRED:
  - `CPIAUCSL`
  - `FEDFUNDS`
  - `PCU3253132531`
  - `DEXBZUS`
  - `WPU023503`
- News: Google News RSS search for coffee market coverage

## Reproducing the Project

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file from `.env.example` and update values if needed.

Required variables:

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_DB`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `MONGO_HOST`
- `MONGO_PORT`
- `MONGO_DB`
- `FRED_API_KEY`
- `PIPELINE_START_DATE`

### 3. Start the databases

```bash
docker compose up -d
```

This initializes:

- MySQL staging tables from `sql/mysql/init_staging.sql`
- PostgreSQL warehouse tables from `sql/postgres/init_warehouse.sql`
- MongoDB without a fixed schema for document storage

### 4. Run the ETL pipeline

```bash
python -m etl.run_pipeline
```

The pipeline will:

- extract coffee futures, weather, macro, and news data
- clear and reload staging tables
- clear and reload MongoDB collections
- build warehouse dimensions and fact tables
- compute analytical features and buy-opportunity scores
- record ETL status in MySQL

### 5. Launch the dashboard

```bash
streamlit run dashboard/Home.py
```

The dashboard includes:

- market overview charts
- buy-opportunity score and driver panels
- cost-pressure summary and owner action center
- margin impact calculator
- information page explaining metrics and data sources
- MongoDB-backed news search page

## Main Implemented Components

### ETL extraction

- `etl/extract/coffee.py`: pulls coffee futures price history
- `etl/extract/weather.py`: pulls daily historical weather by region
- `etl/extract/macro.py`: pulls FRED macroeconomic series
- `etl/extract/news.py`: collects and scrapes coffee news articles

### Transformation and feature engineering

- `etl/transform/build_features.py`: builds dimensions, fact tables, rolling metrics, and logistic-regression buy scores

### Load and orchestration

- `etl/run_pipeline.py`: executes the end-to-end pipeline and database loading process
- `etl/load/load_mongo.py`: writes semi-structured raw data and news to MongoDB

### Dashboard

- `dashboard/Home.py`: main analytics dashboard
- `dashboard/pages/1_Information.py`: metric and source documentation page
- `dashboard/pages/2_News.py`: searchable news interface backed by MongoDB

## Query Demonstration

Representative analytical SQL examples are included in `docs/query_demo.sql`.

## Submission Documents

- `README.md`
- `docs/PROJECT_REPORT.md`
- `docs/FUNCTION_REFERENCE.md`
- `docs/REQUIREMENTS_AUDIT.md`
- source code in the repository

## Notes and Known Limitations

- The project is centered on coffee market intelligence rather than a broad all-asset warehouse covering stocks, bonds, real estate, and energy simultaneously.
- `etl/load/load_mysql.py` and `etl/load/load_postgres.py` are placeholders because loading is handled directly with `pandas.to_sql()` in `etl/run_pipeline.py`.
- `notebooks/demo.ipynb` is currently empty and is not required for reproducing the main results.

## Recommended Submission Packaging

To create a ZIP for submission from the repository root:

```bash
zip -r coffee_warehouse_submission.zip . -x "*.git*" "*__pycache__*" "*.DS_Store"
```
