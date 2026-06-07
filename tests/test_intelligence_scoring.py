import pandas as pd

from nlp.intelligence_scoring import (
    calculate_relevance_score,
    detect_market_sentiment,
)


def main():
    df = pd.read_csv("output/final_intelligence_articles.csv")

    rows = []

    for _, row in df.iterrows():
        article = row.to_dict()

        sentiment = detect_market_sentiment(article)
        relevance_score = calculate_relevance_score(article)

        rows.append(
            {
                "title": article.get("title", ""),
                "primary_company": article.get("primary_company", ""),
                "event_type": article.get("event_type", ""),
                "sentiment": sentiment,
                "relevance_score_1_to_5": relevance_score,
            }
        )

    result_df = pd.DataFrame(rows)

    print(result_df)


if __name__ == "__main__":
    main()