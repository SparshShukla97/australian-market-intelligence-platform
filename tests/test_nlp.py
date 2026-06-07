import pandas as pd
from nlp.pipeline import preprocess_article_record

# Load your RSS output file
df = pd.read_csv("output/rss_articles.csv")

# Take a few articles for testing
test_df = df.head(3).copy()

# IMPORTANT:
# Since your CSV does NOT yet contain full article text,
# we temporarily use summary as a fallback
if "full_text" not in test_df.columns:
    test_df["full_text"] = test_df["summary"].fillna("")

for _, row in test_df.iterrows():
    article = row.to_dict()

    result = preprocess_article_record(article)

    print("\n" + "=" * 100)
    print("TITLE:", result["title"])
    print("SOURCE:", result["source"])
    print("DATE:", result["date"])
    print("URL:", result["url"])

    print("\nPREPROCESS HINTS:", result["preprocess_hints"])

    print("\nCLEANED TEXT PREVIEW:\n")
    print(result["cleaned_text"][:1000])