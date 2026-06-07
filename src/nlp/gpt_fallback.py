
import json
import os
from typing import Dict

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_NAME = "gpt-4o-mini"


def build_article_text(article: Dict) -> str:
    title = article.get("title", "")
    cleaned_text = article.get("cleaned_text", "")

    text = f"TITLE:\n{title}\n\nARTICLE:\n{cleaned_text}"

    return text[:6000]


def extract_with_gpt(article: Dict) -> Dict:
    article_text = build_article_text(article)

    prompt = f"""
You are extracting structured market intelligence from a business news article.

Return only valid JSON with these fields:
- primary_company
- people
- locations
- money_amounts
- event_type
- polished_summary
- key_insight
- why_it_matters

Rules:
- primary_company must be the main company or organisation the article is about.
- event_type must be one of: Funding, Acquisition, Partnership, Expansion, Regulation / Legal, Policy / Economy, Technology / AI, Market Trend, General Business Update.
- polished_summary must summarise the article in 2 clear sentences.
- key_insight must be one clear sentence.
- why_it_matters must explain the business/investor importance in one sentence.
- Return lists for people, locations, and money_amounts.

{article_text}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are a precise market intelligence extraction assistant.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content

    try:
        result = json.loads(content)

        if isinstance(result.get("people"), str):
            result["people"] = [result["people"]]

        if isinstance(result.get("locations"), str):
            result["locations"] = [result["locations"]]

        if isinstance(result.get("money_amounts"), (int, float, str)):
            result["money_amounts"] = [result["money_amounts"]]

        return result

    except json.JSONDecodeError:
        return {
            "primary_company": "",
            "people": [],
            "locations": [],
            "money_amounts": [],
            "event_type": "General Business Update",
            "polished_summary": "",
            "key_insight": "",
            "why_it_matters": "",
        }