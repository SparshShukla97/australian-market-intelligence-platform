import os
import pandas as pd

from source_config import CATEGORY_SOURCES
from rss_fetcher import fetch_articles_from_rss
from scraper import scrape_article_text
from nlp.pipeline import preprocess_article_record


# Minimum suitability score required per category
CATEGORY_THRESHOLDS = {
    "Technology":    16,
    "Funding":       20,
    "Energy":        22,
    "Retail":        18,
    "Property":      20,
    "Policy_Economy": 20,
}

MIN_ARTICLES = 10
MAX_ARTICLES = 20


def remove_duplicates(articles):
    """Remove articles with duplicate URLs, keeping the first occurrence."""
    seen_urls = set()
    unique_articles = []

    for article in articles:
        url = article.get("url", "").strip()
        if not url:
            continue
        if url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)

    return unique_articles


def run_category_pipeline(category: str) -> pd.DataFrame:
    """
    Runs the full fetch → scrape → NLP → filter pipeline for one category.

    Returns a pandas DataFrame of the top articles for that category.
    Returns an empty DataFrame if no articles are found or the category is invalid.
    """
    if category not in CATEGORY_SOURCES:
        print(f"Unknown category: '{category}'. Check source_config.py for valid names.")
        return pd.DataFrame()

    selected_sources = CATEGORY_SOURCES[category]
    all_articles = []

    # =========================
    # STEP 1: FETCH ARTICLES
    # =========================
    for source in selected_sources:
        print(f"\nFetching articles from: {source['source_name']}")

        articles = fetch_articles_from_rss(
            source_name=source["source_name"],
            rss_url=source["rss_url"],
            category=category,
        )

        print(f"Found {len(articles)} articles from {source['source_name']}")
        all_articles.extend(articles)

    if not all_articles:
        print(f"\nNo articles found for category: {category}")
        return pd.DataFrame()

    # =========================
    # STEP 2: REMOVE DUPLICATES
    # =========================
    all_articles = remove_duplicates(all_articles)
    print(f"\nAfter removing duplicates: {len(all_articles)} articles")

    processed_articles = []

    # =========================
    # STEP 3: SCRAPE + NLP
    # =========================
    for article in all_articles:
        try:
            print(f"\nProcessing: {article['title']}")

            # Scrape full text
            raw_text = scrape_article_text(article["url"])
            article["full_text"] = raw_text

            # Preprocess + suitability scoring
            processed = preprocess_article_record(article)

            article.update({
                "cleaned_text":          processed["cleaned_text"],
                "business_signal_count": processed["preprocess_hints"]["business_signal_count"],
                "suitability_score":     processed["suitability"]["suitability_score"],
                "is_suitable":           processed["suitability"]["is_suitable"],
            })

            processed_articles.append(article)

        except Exception as e:
            print(f"Error processing article: {e}")

    if not processed_articles:
        return pd.DataFrame()

    # =========================
    # STEP 4: CONVERT TO DF
    # =========================
    df = pd.DataFrame(processed_articles)

    # =========================
    # STEP 5: FILTER + RANK
    # =========================
    threshold = CATEGORY_THRESHOLDS.get(category, 20)

    df = df[df["suitability_score"] >= threshold]
    df = df.sort_values(by=["suitability_score", "business_signal_count"], ascending=False)

    # Always return at least MIN_ARTICLES if available, cap at MAX_ARTICLES
    if len(df) < MIN_ARTICLES:
        df = df.sort_values(by="suitability_score", ascending=False).head(MIN_ARTICLES)
    else:
        df = df.head(MAX_ARTICLES)

    return df


def main():
    """
    Interactive entry point: prompts the user to pick one category,
    runs the pipeline for it, and saves to output/final_articles.csv.
    """
    print("\nAvailable categories:")
    for category in CATEGORY_SOURCES.keys():
        print(f"  - {category}")

    selected_category = input("\nEnter a category exactly as shown above: ").strip()

    if selected_category not in CATEGORY_SOURCES:
        print("Invalid category selected.")
        return

    df = run_category_pipeline(selected_category)

    if df.empty:
        print("\nNo articles found.")
        return

    # =========================
    # STEP 6: SAVE OUTPUT
    # =========================
    os.makedirs("output", exist_ok=True)
    output_path = os.path.join("output", "final_articles.csv")
    df.to_csv(output_path, index=False)

    print(f"\n✅ Final {len(df)} high-quality articles saved to: {output_path}")


if __name__ == "__main__":
    main()