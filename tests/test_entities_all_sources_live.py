import os
import pandas as pd

from source_config import CATEGORY_SOURCES
from rss_fetcher import fetch_articles_from_rss
from scraper import scrape_article_text
from nlp.pipeline import preprocess_article_record
from nlp.entities import extract_entities_from_text

# How many articles to test from each source
ARTICLES_PER_SOURCE = 2

# Where to save results
os.makedirs("output", exist_ok=True)
OUTPUT_FILE = "output/entities_live_test_summary.csv"

results = []

for category, sources in CATEGORY_SOURCES.items():
    print("\n" + "#" * 120)
    print(f"TESTING CATEGORY: {category}")
    print("#" * 120)

    for source in sources:
        source_name = source["source_name"]
        rss_url = source["rss_url"]

        print("\n" + "=" * 100)
        print(f"FETCHING SOURCE: {source_name}")
        print("=" * 100)

        articles = fetch_articles_from_rss(
            source_name=source_name,
            rss_url=rss_url,
            category=category
        )

        # take only the first few fresh articles
        articles = articles[:ARTICLES_PER_SOURCE]

        if not articles:
            print("No articles fetched.")
            continue

        for article in articles:
            title = article.get("title", "")
            url = article.get("url", "")

            print(f"\nTITLE: {title}")
            print(f"URL: {url}")

            try:
                # scrape full article text
                raw_text = scrape_article_text(url)
                article["full_text"] = raw_text

                # preprocess
                processed = preprocess_article_record(article)
                cleaned_text = processed["cleaned_text"]

                # entity extraction
                entities = extract_entities_from_text(
                    cleaned_text,
                    title=article["title"]
                )

                raw_length = len(raw_text) if raw_text else 0
                cleaned_length = len(cleaned_text) if cleaned_text else 0

                print("Organizations:", entities["organizations"])
                print("People:", entities["people"])
                print("Locations:", entities["locations"])
                print("Money:", entities["money"])

                results.append({
                    "category": category,
                    "source": source_name,
                    "title": title,
                    "url": url,
                    "raw_length": raw_length,
                    "cleaned_length": cleaned_length,
                    "business_signal_count": processed["preprocess_hints"]["business_signal_count"],
                    "noise_signal_count": processed["preprocess_hints"]["noise_signal_count"],
                    "organizations": " | ".join(entities["organizations"]),
                    "people": " | ".join(entities["people"]),
                    "locations": " | ".join(entities["locations"]),
                    "money": " | ".join(entities["money"]),
                    "scrape_success": raw_length > 0,
                    "clean_success": cleaned_length > 0,
                })

            except Exception as e:
                print(f"Error testing article: {e}")

                results.append({
                    "category": category,
                    "source": source_name,
                    "title": title,
                    "url": url,
                    "raw_length": 0,
                    "cleaned_length": 0,
                    "business_signal_count": None,
                    "noise_signal_count": None,
                    "organizations": "",
                    "people": "",
                    "locations": "",
                    "money": "",
                    "scrape_success": False,
                    "clean_success": False,
                })

# save summary
summary_df = pd.DataFrame(results)
summary_df.to_csv(OUTPUT_FILE, index=False)

print("\n" + "=" * 120)
print(f"Saved live test summary to: {OUTPUT_FILE}")
print("=" * 120)