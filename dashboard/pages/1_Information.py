import streamlit as st

st.set_page_config(page_title="Information", layout="wide")

st.title("Information")
st.markdown("""
This page explains the data sources, metrics, and meaning of the values shown in the Coffee Market Intelligence Dashboard.
""")

st.markdown("---")
st.header("Data Sources")

st.markdown("""
### 1. Coffee Futures Market Data
- **Source:** Yahoo Finance via `yfinance`
- **Ticker used:** `KC=F`
- **What it provides:** historical coffee futures prices
- **Metric used on the dashboard:** daily closing futures price in **cents per pound**

### 2. Weather Data
- **Source:** Open-Meteo Historical Weather API
- **Locations used in this dashboard:** São Paulo, Belo Horizonte, and Vitória, Brazil
- **What it provides:** daily average temperature and daily precipitation
- **Metrics used on the dashboard:**
  - average temperature in **°C**
  - precipitation in **millimeters (mm)**

When the dashboard is set to **All Regions**, the weather-based signals are averaged across these Brazil coffee-region proxies.

### 3. Macroeconomic Data
- **Source:** FRED (Federal Reserve Economic Data)
- **Series used:** `CPIAUCSL`, `FEDFUNDS`, `PCU3253132531`, `DEXBZUS`, `WPU023503`
- **What it provides:** inflation, interest-rate, fertilizer, exchange-rate, and dairy-input signals over time
- **Metrics used on the dashboard:**
  - CPI as an **inflation index**, not a dollar amount
  - Fed Funds Rate as a **percent interest rate**
  - Fertilizer Price Index as an **input-cost index proxy** for agriculture
  - BRL/USD as a **Brazil export and currency-pressure proxy**
  - Milk Price Index as a **coffee shop dairy-cost proxy**

### 4. Prediction Layer
- **Method used:** logistic regression trained during the ETL process
- **Prediction target:** whether coffee futures will be higher **7 days later**
- **Core inputs used:** recent coffee momentum, volatility, multi-region weather, fertilizer price changes, milk-price changes, BRL/USD moves, CPI, and Fed Funds
- **Output shown on the dashboard:** a **Buy Opportunity Score** from 0 to 100
- **Driver panel shown on the dashboard:** grouped explanatory buckets for momentum, weather stress, input costs, and macro/FX conditions

### 5. History Window
- The ETL can now pull a longer historical window using the `PIPELINE_START_DATE` environment variable
- More historical rows generally improve the buy-score model by giving it more market regimes to learn from
- If `PIPELINE_START_DATE` is not set, the pipeline now defaults to **2016-01-01**
""")

st.markdown("---")
st.header("What the Metrics Mean")

st.markdown("""
### Coffee Futures Close
This is the **end-of-day closing price** for coffee futures.

- It is **not a stock price**
- It is **not the retail price of coffee in a store**
- It is usually quoted in **cents per pound**

Example: if the dashboard shows **350.20**, that means:
- **350.20 cents per pound**
- or **$3.5020 per pound**

### 7-Day Avg Futures Price
This is the average of the last 7 daily coffee futures closing prices.

It helps smooth daily ups and downs so the short-term trend is easier to see.

### Average Temperature
This is the average daily temperature from the selected weather region.

It is included because weather can influence crop conditions, supply expectations, and commodity markets.

### Total Precipitation
This is the rainfall amount over the displayed period, measured in **millimeters**.

Rainfall matters because agricultural output can be affected by unusually dry or wet conditions.

### CPI Index
**CPI** stands for **Consumer Price Index**.

- It is **not money**
- It is **not a dollar amount**
- It is an **index number** used to track inflation over time

Higher CPI values mean the overall consumer price level is higher relative to the index base period.

### Fed Funds Rate
This is the **effective federal funds rate** from FRED.

It provides a simple view of the broader interest-rate environment that can influence financing conditions, inventory costs, and commodity markets.

### Fertilizer Price Index
This is a **producer price index for fertilizer manufacturing** from FRED.

- It is an **index number**, not a spot cash price
- It is included as a proxy for **agricultural input costs**
- Higher values can indicate more expensive fertilizer conditions for the broader agricultural sector

### BRL/USD Exchange Rate
This is the **Brazilian real to U.S. dollar exchange rate** from FRED.

- It helps provide context for Brazilian export incentives
- A stronger real can sometimes support higher dollar-denominated coffee prices
- A weaker real can sometimes soften that pressure

### Milk Price Index
This is a **producer price index for liquid milk products** from FRED.

- It is used here as a proxy for **dairy input pressure** that matters to coffee shops
- It does not represent the exact wholesale milk price a specific cafe pays
- It helps the dashboard connect commodity buying decisions to cafe-level cost pressure

### Buy Opportunity Score
This is an **experimental prediction score** created inside the ETL pipeline.

- It estimates the probability that coffee prices will be **higher 7 days from now**
- Higher scores suggest buying now may be more attractive for a short-term buyer
- It is a **decision-support indicator**, not financial advice

The dashboard also translates the score into a simple signal:
- **Buy Now** for stronger upside probability
- **Watch** for a mixed outlook
- **Wait** for weaker upside probability

The **Buy Score Drivers** panel is meant to explain the score at a glance. It is an interpretation layer built from the latest signals, not a formal SHAP-style model explanation.
""")

st.markdown("---")
st.header("How the Data Flows")

st.markdown("""
The dashboard follows a simple ETL pipeline:

1. **Extract**  
   Data is pulled from:
   - Yahoo Finance
   - Open-Meteo
   - FRED

2. **Transform**  
   The data is cleaned, aligned by date, prepared for analysis, and used to generate the experimental buy-opportunity score.

3. **Load**  
   - raw data goes into the staging database
   - transformed data goes into the warehouse tables

4. **Visualize**  
   The dashboard reads the warehouse data and displays charts and metrics.
""")
