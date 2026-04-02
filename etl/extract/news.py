import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timezone


def fetch_article_text(url: str) -> str:
    """
    Fetch article page HTML and try to extract readable paragraph text.
    This is a simple best-effort scraper.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Remove unwanted elements
        for tag in soup(["script", "style", "noscript", "header", "footer", "svg", "nav", "form"]):
            tag.decompose()

        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text(" ", strip=True) for p in paragraphs)

        return text[:20000]  # cap length so documents don't get too large
    except Exception:
        return ""


def fetch_coffee_news_rss(max_articles: int = 20) -> list[dict]:
    """
    Pull coffee-related news from a news RSS search feed.
    This stores semi-structured article documents for MongoDB.
    """
    rss_url = (
        "https://news.google.com/rss/search?"
        "q=coffee%20commodity%20OR%20coffee%20prices%20OR%20coffee%20futures"
        "&hl=en-US&gl=US&ceid=US:en"
    )

    feed = feedparser.parse(rss_url)
    articles = []

    for entry in feed.entries[:max_articles]:
        url = entry.get("link", "")
        article_text = fetch_article_text(url) if url else ""

        articles.append({
            "dataset": "coffee_news",
            "source_type": "news_article",
            "title": entry.get("title", ""),
            "url": url,
            "published": entry.get("published", ""),
            "summary": BeautifulSoup(entry.get("summary", ""), "lxml").get_text(" ", strip=True),
            "source": entry.get("source", {}).get("title", "") if isinstance(entry.get("source"), dict) else "",
            "article_text": article_text,
            "keywords": ["coffee", "commodity", "futures", "market"],
            "document_kind": "scraped_news_article",
            "scraped_at": datetime.now(timezone.utc).isoformat()
        })

    return articles