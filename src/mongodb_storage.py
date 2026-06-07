import os
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

DATABASE_NAME = "australian_market_intelligence"
COLLECTION_NAME = "articles"

INPUT_PATH = "output/final_company_enriched_articles.csv"


def main():
    print("Connecting to MongoDB...")

    client = MongoClient(MONGO_URI)

    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    print("Connected successfully.")

    df = pd.read_csv(INPUT_PATH)

    inserted_count = 0
    updated_count = 0

    for _, row in df.iterrows():
        article = row.to_dict()

        result = collection.update_one(
            {"url": article.get("url")},
            {"$set": article},
            upsert=True,
        )

        if result.upserted_id:
            inserted_count += 1
        else:
            updated_count += 1

    print(f"\nInserted {inserted_count} new articles.")
    print(f"Updated {updated_count} existing articles.")

    print("\nMongoDB storage complete.")


if __name__ == "__main__":
    main()