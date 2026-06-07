import os

import pandas as pd

from nlp.gpt_fallback import extract_with_gpt


INPUT_PATH  = "output/final_intelligence_articles.csv"
OUTPUT_PATH = "output/final_production_articles.csv"


def has_insights(article: dict) -> bool:
    """
    Returns True if the article already has all three AI-generated fields filled.
    Skipping these avoids redundant GPT calls on articles processed in previous runs.
    """
    def filled(val):
        return str(val).strip() not in ("", "nan", "None")

    return (
        filled(article.get("polished_summary"))
        and filled(article.get("key_insight"))
        and filled(article.get("strategic_importance"))
    )


def main():
    if not os.path.exists(INPUT_PATH):
        print(f"Input file not found: {INPUT_PATH}")
        return

    df = pd.read_csv(INPUT_PATH)
    updated_rows = []
    skipped = 0
    processed = 0

    for index, row in df.iterrows():
        article = row.to_dict()

        # Skip articles that already have all AI fields — saves GPT API calls
        if has_insights(article):
            skipped += 1
            updated_rows.append(article)
            continue

        print(f"\nGenerating insights for row {index}: {article.get('title')}")

        gpt_result = extract_with_gpt(article)

        article["polished_summary"]    = gpt_result.get("polished_summary", "")
        article["key_insight"]         = gpt_result.get("key_insight", "")
        article["strategic_importance"] = gpt_result.get("why_it_matters", "")

        updated_rows.append(article)
        processed += 1

    print(f"\n  GPT insights: {processed} new  |  {skipped} already done (skipped)")

    output_df = pd.DataFrame(updated_rows)
    output_df.to_csv(OUTPUT_PATH, index=False)

    print(f"\nSaved production-ready articles to: {OUTPUT_PATH}")
    print(
        output_df[
            [
                "title",
                "primary_company",
                "sentiment",
                "relevance_score",
                "polished_summary",
                "key_insight",
                "strategic_importance",
            ]
        ].head()
    )


if __name__ == "__main__":
    main()