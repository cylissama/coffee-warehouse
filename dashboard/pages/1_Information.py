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
- **Location used in this dashboard:** São Paulo, Brazil *(currently used as a representative proxy location)*
- **What it provides:** daily average temperature and daily precipitation
- **Metrics used on the dashboard:**
  - average temperature in **°C**
  - precipitation in **millimeters (mm)**

### 3. Macroeconomic Data
- **Source:** FRED (Federal Reserve Economic Data)
- **Series used:** `CPIAUCSL`
- **What it provides:** Consumer Price Index values over time
- **Metric used on the dashboard:** CPI as an **inflation index**, not a dollar amount
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
   The data is cleaned, aligned by date, and prepared for analysis.

3. **Load**  
   - raw data goes into the staging database
   - transformed data goes into the warehouse tables

4. **Visualize**  
   The dashboard reads the warehouse data and displays charts and metrics.
""")