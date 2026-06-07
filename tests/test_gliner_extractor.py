import pandas as pd

from nlp.gliner_extractor import extract_with_gliner


def main():
    df = pd.read_csv("output/final_articles.csv")

    for index, row in df.head(5).iterrows():
        title = row.get("title", "")
        cleaned_text = row.get("cleaned_text", "")

        result = extract_with_gliner(title, cleaned_text)

        print("\n" + "=" * 100)
        print(f"ARTICLE {index + 1}")
        print("TITLE:", title)
        print("COMPANIES:", result["gliner_companies"])
        print("PEOPLE:", result["gliner_people"])
        print("LOCATIONS:", result["gliner_locations"])
        print("GOV ORGS:", result["gliner_government_organisations"])
        print("MONEY:", result["gliner_money_amounts"])


if __name__ == "__main__":
    main()