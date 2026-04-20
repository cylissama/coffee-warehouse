import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

st.set_page_config(page_title="Coffee News", layout="wide")


@st.cache_resource
def get_mongo_collection():
    host = os.getenv("MONGO_HOST", "localhost")
    port = int(os.getenv("MONGO_PORT", "27017"))
    db_name = os.getenv("MONGO_DB", "coffee_intelligence")

    client = MongoClient(host=host, port=port)
    db = client[db_name]
    return db["coffee_news_articles"]


def load_news_documents():
    collection = get_mongo_collection()
    docs = list(
        collection.find(
            {},
            {
                "_id": 0,
                "title": 1,
                "source": 1,
                "published": 1,
                "url": 1,
                "summary": 1,
                "article_text": 1,
                "scraped_at": 1,
                "keywords": 1,
            },
        )
    )
    return pd.DataFrame(docs)


st.title("Coffee News")
st.markdown(
    """
This page shows scraped coffee-related news articles stored in MongoDB.

Use the filters below to search article titles, summaries, publishers, and text previews.
"""
)

df = load_news_documents()

if df.empty:
    st.warning("No news articles were found in MongoDB. Run the ETL pipeline first.")
    st.stop()

# Clean up columns
for col in ["title", "source", "published", "url", "summary", "article_text", "scraped_at"]:
    if col not in df.columns:
        df[col] = ""

df["source"] = df["source"].fillna("").replace("", "Unknown")
df["title"] = df["title"].fillna("")
df["summary"] = df["summary"].fillna("")
df["article_text"] = df["article_text"].fillna("")
df["published"] = df["published"].fillna("")
df["url"] = df["url"].fillna("")

st.markdown("---")
st.subheader("Filter Articles")

col1, col2, col3 = st.columns([2, 1, 1])

search_text = col1.text_input(
    "Keyword Search",
    placeholder="Search titles, summaries, or article text..."
)

all_sources = ["All"] + sorted([s for s in df["source"].dropna().unique().tolist() if s])
selected_source = col2.selectbox("Publisher", all_sources, index=0)

max_articles = col3.selectbox("Articles to Show", [5, 10, 20, 50], index=1)

filtered_df = df.copy()

if selected_source != "All":
    filtered_df = filtered_df[filtered_df["source"] == selected_source]

if search_text.strip():
    q = search_text.strip().lower()
    filtered_df = filtered_df[
        filtered_df["title"].str.lower().str.contains(q, na=False)
        | filtered_df["summary"].str.lower().str.contains(q, na=False)
        | filtered_df["article_text"].str.lower().str.contains(q, na=False)
    ]

# Sort by published string descending as a simple first pass
filtered_df = filtered_df.sort_values(by="published", ascending=False).head(max_articles)

st.markdown("---")
st.subheader("Results")
st.write(f"Showing **{len(filtered_df)}** article(s).")

if filtered_df.empty:
    st.info("No articles matched your filters.")
    st.stop()

for i, row in filtered_df.iterrows():
    with st.container():
        st.markdown(f"### {row['title'] if row['title'] else 'Untitled Article'}")
        st.markdown(f"**Source:** {row['source']}")
        st.markdown(f"**Published:** {row['published'] if row['published'] else 'Unknown'}")

        if row["url"]:
            st.markdown(f"[Open Article]({row['url']})")

        if row["summary"]:
            st.markdown("**Summary**")
            st.write(row["summary"])

        preview = row["article_text"][:1200].strip()
        if preview:
            st.markdown("**Article Text Preview**")
            st.write(preview + ("..." if len(row["article_text"]) > 1200 else ""))

        st.markdown("---")

st.subheader("Raw News Data")
st.dataframe(filtered_df, width="stretch")
