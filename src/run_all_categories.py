"""
run_all_categories.py

Runs the full article pipeline across all six categories automatically.
Combines the results into a single deduplicated CSV file.

Usage:
    cd src/
    python run_all_categories.py

Output:
    output/final_all_categories_articles.csv
"""

import os
import pandas as pd

from main import run_category_pipeline


# These must match the keys in source_config.py exactly
CATEGORIES = [
    "Technology",

    "Energy",
    "Retail",
    "Property",
    "Policy_Economy",
]

OUTPUT_PATH = "output/final_all_categories_articles.csv"


def main():
    all_dataframes = []

    for category in CATEGORIES:
        print(f"\n{'=' * 52}")
        print(f"  Running pipeline for: {category}")
        print(f"{'=' * 52}")

        try:
            df = run_category_pipeline(category)

            if df is not None and not df.empty:
                print(f"\n✅ {category}: collected {len(df)} articles")
                all_dataframes.append(df)
            else:
                print(f"\n⚠️  {category}: no articles found, skipping.")

        except Exception as e:
            print(f"\n❌ {category}: pipeline failed — {e}")

    if not all_dataframes:
        print("\nNo articles collected from any category. Nothing to save.")
        return

    # Combine all category DataFrames into one
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    print(f"\nTotal articles before deduplication: {len(combined_df)}")

    # Remove any articles that share the same URL across categories
    combined_df = combined_df.drop_duplicates(subset=["url"])
    print(f"Total articles after deduplication:  {len(combined_df)}")

    # Save combined output
    os.makedirs("output", exist_ok=True)
    combined_df.to_csv(OUTPUT_PATH, index=False)

    print(f"\n✅ Saved {len(combined_df)} articles to: {OUTPUT_PATH}")

    # Summary table
    if "category_requested" in combined_df.columns:
        summary = combined_df.groupby("category_requested").size().reset_index(name="article_count")
        print("\nArticles per category:")
        print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
