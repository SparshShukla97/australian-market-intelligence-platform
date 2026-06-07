import pandas as pd

from nlp.entity_extractor import extract_article_intelligence


def main():
    df = pd.read_csv("output/final_articles.csv")

    for _, row in df.head(25).iterrows():
        article = row.to_dict()
        result = extract_article_intelligence(article)

        print("\n" + "=" * 100)
        print("TITLE:", article.get("title"))
        print("EVENT TYPE:", result["event_type"])
        print("ORGANISATIONS:", result["organisations"])
        print("PEOPLE:", result["people"])
        print("LOCATIONS:", result["locations"])
        print("MONEY:", result["money_amounts"])
        print("CONFIDENCE:", result["confidence_score"])
        print("NEEDS GPT FALLBACK:", result["needs_gpt_fallback"])


if __name__ == "__main__":
    main()