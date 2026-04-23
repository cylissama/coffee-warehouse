# Roadmap

## Goal

Make the project more valuable for coffee shop owners while also deepening the warehouse so each database is used for the kind of work it handles best.

## Product Direction

The next version of the project should evolve from a market-intelligence dashboard into a shop-owner operating console. That means keeping the macro and commodity signals, but connecting them more directly to purchasing, pricing, inventory, and local store decisions.

## Highest-Value Next Features

### 1. Purchasing Planner

Add a planning module that estimates:

- recommended buy timing for beans
- suggested reorder windows
- expected 2-week and 4-week cost pressure
- low, medium, and high scenario bands

Why it matters:

- this converts the current buy score into an operational workflow
- it gives owners a reason to return to the dashboard regularly

Best database usage:

- `PostgreSQL` for historical features, scenario tables, and forecast outputs
- `MySQL` for daily refresh logs and staged vendor price imports

### 2. Drink Margin and Menu Simulator

Expand the current margin calculator into a more complete simulator with:

- drink recipes
- bean usage by drink type
- milk and syrup input costs
- estimated gross margin by menu item
- suggested price changes to maintain target margin

Why it matters:

- this is much closer to how a coffee shop owner actually thinks
- it connects commodity signals to menu decisions

Best database usage:

- `MySQL` for structured operational tables like menu items, recipes, and supplier price sheets
- `PostgreSQL` for aggregated profitability analysis over time

### 3. Local Market Context

Add local demand and operating context such as:

- city-level weather
- seasonal foot-traffic proxies
- holiday calendars
- local inflation snapshots
- cafe sales imports if available

Why it matters:

- a shop owner needs both supply-side and local demand-side context
- it makes the dashboard feel less like a commodity terminal and more like a business tool

Best database usage:

- `PostgreSQL` for time-series joins across local and macro signals
- `MongoDB` for semi-structured external event feeds and local notes

### 4. News Intelligence Upgrade

Extend the news page so it does more than show raw articles:

- topic tagging
- sentiment labels
- source credibility tiers
- article clustering by event
- summaries of what changed this week

Why it matters:

- owners should not need to read every article manually
- this makes MongoDB much more useful than simple storage

Best database usage:

- `MongoDB` for full article documents, extracted entities, summaries, and topic tags
- `PostgreSQL` for storing daily aggregate sentiment metrics used in the dashboard

### 5. Data Explorer for Advanced Users

Add an exploration page for deeper analysis:

- table browser for dimensions and facts
- filterable raw-vs-transformed comparisons
- SQL example gallery
- anomaly flags and audit trails

Why it matters:

- keeps the project strong for class evaluation and technical demos
- shows the warehouse is more than a chart backend

Best database usage:

- `MySQL` for raw staging inspection
- `PostgreSQL` for warehouse exploration
- `MongoDB` for document search and article drill-down

## Using All Databases Better

### MySQL

Current role:

- raw staging tables
- ETL job logging

Ways to use it better:

- supplier catalog and price sheet imports
- store configuration tables
- menu item master data
- recipe and ingredient reference data
- ETL quality-control tables with row counts and validation failures

### PostgreSQL

Current role:

- dimensions and analytical fact tables
- dashboard query source

Ways to use it better:

- forecast tables
- materialized views for common dashboard queries
- monthly and weekly aggregates
- scenario analysis outputs
- historical backtesting results for the buy-score model

### MongoDB

Current role:

- raw documents
- news articles

Ways to use it better:

- NLP-enriched article documents
- scraped supplier notes and market commentary
- store journal entries or owner annotations
- event timeline documents
- competitor price observations from semi-structured web sources

## Recommended Build Order

### Phase 1: Owner Workflow

- purchasing planner
- expanded drink margin simulator
- supplier and recipe tables

### Phase 2: Better Warehouse Depth

- materialized warehouse views
- quality-control and audit tables
- historical model backtesting

### Phase 3: Rich Document Intelligence

- article tagging and sentiment
- event clustering
- weekly narrative summaries

### Phase 4: Local Business Context

- local weather and seasonality
- shop sales upload support
- demand-side comparisons

## Concrete Schema Ideas

### MySQL tables

- `suppliers`
- `supplier_price_history`
- `menu_items`
- `recipes`
- `ingredients`
- `etl_data_quality_checks`

### PostgreSQL tables

- `fact_shop_margin_daily`
- `fact_purchase_recommendations`
- `fact_forecast_scenarios`
- `agg_market_features_weekly`
- `model_backtest_results`

### MongoDB collections

- `coffee_news_enriched`
- `market_event_clusters`
- `supplier_notes`
- `owner_annotations`
- `competitor_price_observations`

## Best Immediate Next Step

If we want the most impact with the least extra complexity, the next feature to build should be:

`Purchasing Planner + Expanded Margin Simulator`

That combination would make the dashboard substantially more useful for a shop owner and would naturally force the project to use:

- `MySQL` for operational inputs
- `PostgreSQL` for forecasting and analytics
- `MongoDB` for unstructured market context
