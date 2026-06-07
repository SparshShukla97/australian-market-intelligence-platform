import pandas as pd
from scraper import scrape_article_text
from nlp.pipeline import preprocess_article_record
from nlp.entities import extract_entities_from_text

ARTICLES_PER_SOURCE = 3

df = pd.read_csv("output/rss_articles.csv")

sources = df["source"].dropna().unique()

for source in sources:
    print("\n" + "#" * 120)
    print(f"TESTING SOURCE: {source}")
    print("#" * 120)

    source_df = df[df["source"] == source].head(ARTICLES_PER_SOURCE)

    for _, row in source_df.iterrows():
        article = row.to_dict()

        print("\n" + "=" * 100)
        print("TITLE:", article["title"])
        print("URL:", article["url"])

        raw_text = scrape_article_text(article["url"])
        article["full_text"] = raw_text

        processed = preprocess_article_record(article)
        cleaned_text = processed["cleaned_text"]

        entities = extract_entities_from_text(cleaned_text, title=article["title"])

        print("\n--- EXTRACTED ENTITIES ---")
        print("Organizations:", entities["organizations"])
        print("People:", entities["people"])
        print("Locations:", entities["locations"])
        print("Money:", entities["money"])