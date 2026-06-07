import json
import os

import pandas as pd

from nlp.gpt_fallback import extract_with_gpt
from nlp.intelligence_scoring import (
    calculate_relevance_score,
    detect_market_sentiment,
)


INPUT_PATH = "output/enriched_articles.csv"
OUTPUT_PATH = "output/final_intelligence_articles.csv"


def to_json_string(value):
    return json.dumps(value, ensure_ascii=False)


def main():
    if not os.path.exists(INPUT_PATH):
        print(f"Input file not found: {INPUT_PATH}")
        return

    df = pd.read_csv(INPUT_PATH)
    updated_rows = []

    for index, row in df.iterrows():
        article = row.to_dict()

        article["sentiment"] = detect_market_sentiment(article)
        article["relevance_score"] = calculate_relevance_score(article)

        article["polished_summary"] = ""
        article["key_insight"] = ""
        article["strategic_importance"] = ""
        article["used_gpt_fallback"] = False

        needs_fallback = article.get("needs_gpt_fallback", False)

        if needs_fallback is True or str(needs_fallback).lower() == "true":
            print(f"\nRunning GPT fallback for row {index}: {article.get('title')}")

            gpt_result = extract_with_gpt(article)

            article["primary_company"] = gpt_result.get(
                "primary_company",
                article.get("primary_company", ""),
            )
            article["people"] = to_json_string(gpt_result.get("people", []))
            article["locations"] = to_json_string(gpt_result.get("locations", []))
            article["money_amounts"] = to_json_string(gpt_result.get("money_amounts", []))
            article["event_type"] = gpt_result.get(
                "event_type",
                article.get("event_type", ""),
            )

            article["polished_summary"] = gpt_result.get("polished_summary", "")
            article["key_insight"] = gpt_result.get("key_insight", "")
            article["strategic_importance"] = gpt_result.get("why_it_matters", "")
            article["used_gpt_fallback"] = True

        updated_rows.append(article)

    output_df = pd.DataFrame(updated_rows)
    os.makedirs("output", exist_ok=True)
    output_df.to_csv(OUTPUT_PATH, index=False)

    print(f"\nSaved final intelligence output to: {OUTPUT_PATH}")
    print(
        output_df[
            [
                "title",
                "primary_company",
                "event_type",
                "sentiment",
                "relevance_score",
                "needs_gpt_fallback",
                "used_gpt_fallback",
            ]
        ]
    )


if __name__ == "__main__":
    main()