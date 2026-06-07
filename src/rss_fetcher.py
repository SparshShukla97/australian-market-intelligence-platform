import feedparser
import requests
from typing import List, Dict

MAX_ARTICLES_PER_SOURCE = 30


def fetch_articles_from_rss(source_name: str, rss_url: str, category: str) -> List[Dict]:
    """
    Fetch article metadata from a single RSS feed.
    Returns a list of dictionaries.
    """
    articles = []

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "application/rss+xml, application/xml;q=0.9,*/*;q=0.8",
        }

        response = requests.get(rss_url, headers=headers, timeout=10)
        response.raise_for_status()

        feed = feedparser.parse(response.content)

        for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:

            title = entry.get("title", "").strip()
            url = entry.get("link", "").strip()

            # Skip bad entries
            if not title or not url:
                continue

            article = {
                "source": source_name,
                "source_type": "rss",
                "category_requested": category,
                "title": title,
                "url": url,
                "published_date": entry.get("published", "").strip(),
                "summary": entry.get("summary", "").strip()
            }

            articles.append(article)

        

    except requests.exceptions.Timeout:
        print(f"Timeout while fetching {source_name}")
    except Exception as e:
        print(f"Error fetching articles from {source_name}: {e}")

    return articles