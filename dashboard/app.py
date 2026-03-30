import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

pg_engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)

st.title("Coffee Market Intelligence Demo")

query = """
SELECT date_id, coffee_close, avg_temp, precipitation, cpi_value, coffee_7day_ma
FROM fact_market_summary
ORDER BY date_id;
"""

df = pd.read_sql(query, pg_engine)

st.subheader("Warehouse Data")
st.dataframe(df)

st.subheader("Coffee Close Price")
st.line_chart(df.set_index("date_id")["coffee_close"])

st.subheader("Coffee 7-Day Moving Average")
st.line_chart(df.set_index("date_id")["coffee_7day_ma"])

st.subheader("Temperature")
st.line_chart(df.set_index("date_id")["avg_temp"])