import json
import os

import pandas as pd

from nlp.entity_extractor import extract_article_intelligence


def to_json_string(value):
    return json.dumps(value, ensure_ascii=False)


def main():
    input_path = "output/final_articles.csv"
    output_path = "output/entity_validation_results.csv"

    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return

    df = pd.read_csv(input_path)
    results = []

    for _, row in df.iterrows():
        article = row.to_dict()
        extracted = extract_article_intelligence(article)

        results.append(
            {
                "source": article.get("source", ""),
                "category_requested": article.get("category_requested", ""),
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "primary_company": extracted.get("primary_company", ""),
                "event_type": extracted.get("event_type", ""),
                "organisations": to_json_string(extracted.get("organisations", [])),
                "people": to_json_string(extracted.get("people", [])),
                "locations": to_json_string(extracted.get("locations", [])),
                "money_amounts": to_json_string(extracted.get("money_amounts", [])),
                "confidence_score": extracted.get("confidence_score", 0),
                "needs_gpt_fallback": extracted.get("needs_gpt_fallback", True),
            }
        )

    output_df = pd.DataFrame(results)
    os.makedirs("output", exist_ok=True)
    output_df.to_csv(output_path, index=False)

    print(f"Saved {len(output_df)} validation rows to: {output_path}")
    print(output_df[["title", "primary_company", "event_type", "confidence_score", "needs_gpt_fallback"]])


if __name__ == "__main__":
    main()