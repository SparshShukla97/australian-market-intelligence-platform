from gliner import GLiNER
import pandas as pd


MODEL_NAME = "urchade/gliner_medium-v2.1"

LABELS = [
    "company",
    "person",
    "location",
    "government organization",
    "money",
]


def main():
    print("Loading GLiNER model...")
    model = GLiNER.from_pretrained(MODEL_NAME)

    df = pd.read_csv("output/final_articles.csv")

    article = df.iloc[0]

    title = article.get("title", "")
    cleaned_text = article.get("cleaned_text", "")

    full_text = f"{title}. {cleaned_text}"

    print("\nTITLE:")
    print(title)

    print("\nRunning GLiNER extraction...\n")

    entities = model.predict_entities(
        full_text,
        labels=LABELS,
    )

    for entity in entities:
        print(
            f"Text: {entity['text']} | "
            f"Label: {entity['label']} | "
            f"Score: {round(entity['score'], 3)}"
        )


if __name__ == "__main__":
    main()