from scraper import scrape_article_text
from nlp.pipeline import preprocess_article_record
from nlp.entities import extract_entities_from_text


# We test on real articles from different sources
TEST_ARTICLES = [
    {
        "title": "NRF takes $10m stake in AI bottleneck buster Syenta",
        "source": "InnovationAus",
        "published_date": "Tue, 21 Apr 2026 13:01:40 +0000",
        "url": "https://www.innovationaus.com/nrf-takes-10m-stake-in-chip-bottleneck-buster-syenta/",
        "category_requested": "Technology",
    },
    {
        "title": "ANU spinout raises $36 million Series A to make AI chips",
        "source": "Startup Daily",
        "published_date": "Tue, 21 Apr 2026 22:09:35 +0000",
        "url": "https://www.startupdaily.net/topic/funding/anu-spinout-raises-36-million-series-a-to-make-ai-chips/",
        "category_requested": "Technology",
    },
    {
        "title": "NEXTDC to raise $1.5 billion to accelerate Sydney data centre rollout",
        "source": "IT News",
        "published_date": "Tue, 21 Apr 2026 06:36:00 +1000",
        "url": "https://www.itnews.com.au/news/nextdc-to-raise-15-billion-to-accelerate-sydney-data-centre-rollout-625218?utm_source=feed&utm_medium=rss&utm_campaign=iTnews+",
        "category_requested": "Technology",
    },
]


for article in TEST_ARTICLES:
    print("\n" + "=" * 120)
    print("TITLE:", article["title"])
    print("SOURCE:", article["source"])
    print("URL:", article["url"])

    # Step 1: scrape full article text
    raw_text = scrape_article_text(article["url"])
    article["full_text"] = raw_text

    # Step 2: preprocess article text
    processed = preprocess_article_record(article)
    cleaned_text = processed["cleaned_text"]

    # Step 3: run entity extraction
    entities = extract_entities_from_text(cleaned_text, title=article["title"])

    print("\n--- CLEANED TEXT PREVIEW ---\n")
    print(cleaned_text[:1200] if cleaned_text else "NO CLEANED TEXT")

    print("\n--- EXTRACTED ENTITIES ---\n")
    print("Organizations:", entities["organizations"])
    print("People:", entities["people"])
    print("Locations:", entities["locations"])
    print("Money:", entities["money"])