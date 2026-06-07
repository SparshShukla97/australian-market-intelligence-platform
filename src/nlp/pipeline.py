from typing import Dict
from .preprocess import clean_article_text, build_preprocess_hints
from .suitability import evaluate_article_suitability


def preprocess_article_record(article: Dict) -> Dict:
    """
    Clean article text and add preprocessing + suitability signals.
    """
    title = article.get("title", "")
    source = article.get("source", "")
    published_date = article.get("published_date", "")
    url = article.get("url", "")
    category = article.get("category_requested", "")
    full_text = article.get("full_text", "")

    cleaned_text = clean_article_text(full_text)

    preprocess_hints = build_preprocess_hints(
        title=title,
        text=cleaned_text
    )

    suitability = evaluate_article_suitability(
        title=title,
        source=source,
        cleaned_text=cleaned_text,
        category=article.get("category_requested", "")
    )

    return {
        "title": title,
        "source": source,
        "date": published_date,
        "url": url,
        "category": category,
        "raw_text": full_text,
        "cleaned_text": cleaned_text,
        "preprocess_hints": preprocess_hints,
        "suitability": suitability,
    }