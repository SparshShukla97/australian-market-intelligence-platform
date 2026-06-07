# Import your article scraper
from scraper import scrape_article_text

# Import the preprocessing pipeline function
from nlp.pipeline import preprocess_article_record


# We manually define a few real articles to test.
# These are good because they are from different sources.
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


# Loop through each test article one by one
for article in TEST_ARTICLES:
    print("\n" + "=" * 120)
    print("TITLE:", article["title"])
    print("SOURCE:", article["source"])
    print("URL:", article["url"])

    # Step 1:
    # Use your scraper to extract the full article text from the URL
    raw_text = scrape_article_text(article["url"])

    # Add the scraped text into the article dictionary
    # so the pipeline can process it
    article["full_text"] = raw_text

    # Step 2:
    # Run the preprocessing pipeline on the article
    result = preprocess_article_record(article)

    # Step 3:
    # Show the raw article text before preprocessing
    print("\n--- RAW TEXT PREVIEW ---\n")
    print(raw_text[:1200] if raw_text else "NO RAW TEXT EXTRACTED")

    # Step 4:
    # Show the cleaned article text after preprocessing
    print("\n--- CLEANED TEXT PREVIEW ---\n")
    print(result["cleaned_text"][:1200] if result["cleaned_text"] else "NO CLEANED TEXT")

    # Step 5:
    # Show the soft preprocessing hints
    print("\n--- PREPROCESS HINTS ---\n")
    print(result["preprocess_hints"])