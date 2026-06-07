import json
import os

import pandas as pd

from nlp.entity_extractor import extract_article_intelligence


# Prefer the all-categories file when it exists (produced by run_all_categories.py).
# Falls back to the single-category file produced by main.py.
ALL_CATEGORIES_PATH = "output/final_all_categories_articles.csv"
SINGLE_CATEGORY_PATH = "output/final_articles.csv"

INPUT_PATH = (
    ALL_CATEGORIES_PATH
    if os.path.exists(ALL_CATEGORIES_PATH)
    else SINGLE_CATEGORY_PATH
)

OUTPUT_PATH = "output/enriched_articles.csv"


def to_json_string(value):
    return json.dumps(value, ensure_ascii=False)


def main():
    if not os.path.exists(INPUT_PATH):
        print(f"Input file not found: {INPUT_PATH}")
        return

    df = pd.read_csv(INPUT_PATH)

    enriched_rows = []

    for _, row in df.iterrows():
        article = row.to_dict()
        extracted = extract_article_intelligence(article)

        enriched_article = article.copy()

        enriched_article["primary_company"] = extracted["primary_company"]
        enriched_article["event_type"] = extracted["event_type"]
        enriched_article["organisations"] = to_json_string(extracted["organisations"])
        enriched_article["people"] = to_json_string(extracted["people"])
        enriched_article["locations"] = to_json_string(extracted["locations"])
        enriched_article["money_amounts"] = to_json_string(extracted["money_amounts"])
        enriched_article["confidence_score"] = extracted["confidence_score"]
        enriched_article["needs_gpt_fallback"] = extracted["needs_gpt_fallback"]

        enriched_rows.append(enriched_article)

    output_df = pd.DataFrame(enriched_rows)

    os.makedirs("output", exist_ok=True)
    output_df.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved {len(output_df)} enriched articles to: {OUTPUT_PATH}")
    print(
        output_df[
            [
                "title",
                "primary_company",
                "event_type",
                "confidence_score",
                "needs_gpt_fallback",
            ]
        ]
    )


if __name__ == "__main__":
    main()