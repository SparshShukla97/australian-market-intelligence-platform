import pandas as pd

from nlp.gpt_fallback import extract_with_gpt


def main():
    df = pd.read_csv("output/enriched_articles.csv")

    flagged = df[df["needs_gpt_fallback"] == True]

    if flagged.empty:
        print("No GPT fallback rows found.")
        return

    article = flagged.iloc[0].to_dict()

    print("Testing GPT fallback on:")
    print(article["title"])

    result = extract_with_gpt(article)

    print("\nGPT RESULT:")
    print(result)


if __name__ == "__main__":
    main()