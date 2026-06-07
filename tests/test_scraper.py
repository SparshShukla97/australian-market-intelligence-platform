import pandas as pd
from scraper import scrape_article_text

df = pd.read_csv("output/rss_articles.csv")

sources_to_test = ["SBS News Australia", "The Australia Institute"]

for source_name in sources_to_test:
    test_df = df[df["source"] == source_name].head(2)

    if test_df.empty:
        print(f"\nNo articles found for {source_name}")
        continue

    print("\n" + "#" * 110)
    print(f"TESTING SOURCE: {source_name}")
    print("#" * 110)

    for _, row in test_df.iterrows():
        print("\n" + "=" * 100)
        print(f"Source: {row['source']}")
        print(f"Testing article: {row['title']}")
        print(f"URL: {row['url']}\n")

        article_text = scrape_article_text(row["url"])

        if article_text:
            print("Extraction successful.")
            print(f"Extracted length: {len(article_text)} characters")
            print("\nPreview:\n")
            print(article_text[:1500])
        else:
            print("Extraction failed.")