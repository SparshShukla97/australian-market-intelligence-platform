"""
company_image_enrichment.py

Fetches hero images for each article's primary company from Wikipedia.
Stores results as optional fields in MongoDB:
  - company_hero_image_url   : full-resolution image from Wikipedia
  - company_wikipedia_url    : link to the Wikipedia page

Only fetches articles that don't already have a hero image (incremental).
Respects Wikipedia's rate limits with a small delay between requests.

Usage:
    PYTHONPATH=src python src/company_image_enrichment.py
"""

import os
import time
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME     = "australian_market_intelligence"
COLLECTION  = "articles"

# Wikipedia REST API — no key needed, just a User-Agent header
WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
HEADERS = {"User-Agent": "AusMarketIntelBot/1.0 (research project)"}
DELAY_BETWEEN_REQUESTS = 0.4   # seconds — stay well within rate limits


# Companies that don't have Wikipedia pages (skip to save time)
SKIP_COMPANIES = {
    "", "nan", "None", "N/A",
    "Australian Government", "Federal Budget", "Budget", "Labor", "Labour",
    "Labor Party", "First Nations", "JobSeeker", "Medicare",
    "The Australian Government", "NSW Police", "Digital Canberra",
    "National Electricity Market", "NEM (National Electricity Market)",
    "Working Australians", "Baby Boomers",
}


def fetch_wikipedia_image(company_name: str) -> dict:
    """
    Fetch the hero image and Wikipedia URL for a company.
    Returns dict with 'image_url' and 'wikipedia_url', or empty strings on failure.
    """
    title = company_name.strip().replace(" ", "_")
    url   = WIKI_SUMMARY_URL.format(title=requests.utils.quote(title, safe=""))

    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code != 200:
            return {"image_url": "", "wikipedia_url": ""}

        data     = resp.json()
        # Prefer original full-res image, fall back to thumbnail
        image    = (
            data.get("originalimage", {}).get("source", "")
            or data.get("thumbnail",  {}).get("source", "")
        )
        wiki_url = (
            data.get("content_urls", {})
                .get("desktop",       {})
                .get("page",          "")
        )
        return {"image_url": image, "wikipedia_url": wiki_url}

    except Exception:
        return {"image_url": "", "wikipedia_url": ""}


def main():
    client     = MongoClient(MONGO_URI)
    collection = client[DB_NAME][COLLECTION]

    # Only process articles missing a hero image (incremental — skip already done)
    query = {
        "$or": [
            {"company_hero_image_url": {"$exists": False}},
            {"company_hero_image_url": ""},
            {"company_hero_image_url": None},
        ]
    }

    articles = list(collection.find(query, {"_id": 1, "primary_company": 1}))
    total    = len(articles)

    if total == 0:
        print("  All articles already have hero images. Nothing to do.")
        return

    print(f"  Fetching hero images for {total} articles...")

    # Deduplicate companies so we don't hit Wikipedia for the same company twice
    seen_companies: dict = {}   # company_name → {"image_url", "wikipedia_url"}
    updated = 0
    skipped = 0

    for i, doc in enumerate(articles, 1):
        company = str(doc.get("primary_company", "")).strip()

        if company in SKIP_COMPANIES:
            skipped += 1
            continue

        # Reuse result if we already looked this company up
        if company not in seen_companies:
            result = fetch_wikipedia_image(company)
            seen_companies[company] = result
            time.sleep(DELAY_BETWEEN_REQUESTS)
        else:
            result = seen_companies[company]

        # Update MongoDB even if image_url is empty (marks as "attempted")
        collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {
                "company_hero_image_url": result["image_url"],
                "company_wikipedia_url":  result["wikipedia_url"],
            }}
        )

        if result["image_url"]:
            updated += 1

        if i % 10 == 0 or i == total:
            print(f"    {i}/{total} processed — {updated} images found")

    print(f"\n  Done: {updated} hero images fetched, {skipped} skipped (no Wikipedia page)")


if __name__ == "__main__":
    main()
