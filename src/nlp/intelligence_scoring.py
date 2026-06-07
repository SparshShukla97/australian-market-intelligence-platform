from typing import Dict, List


POSITIVE_EVENT_TYPES = {
    "Funding",
    "Partnership",
    "Expansion",
    "Technology / AI",
}

NEGATIVE_EVENT_TYPES = {
    "Regulation / Legal",
}

HIGH_VALUE_EVENT_TYPES = {
    "Funding",
    "Acquisition",
    "Partnership",
    "Expansion",
    "Regulation / Legal",
    "Policy / Economy",
    "Technology / AI",
}


POSITIVE_KEYWORDS = [
    "raised",
    "raises",
    "secured",
    "backing",
    "spinout",
    "funding",
    "investment",
    "grant",
    "growth",
    "expansion",
    "expanded",
    "launch",
    "partnership",
    "deal",
    "contract",
    "approval",
    "profit",
    "revenue growth",
    "record",
    "surge",
    "boost",
    "successful",
    "innovation",
    "modernisation",
    "saves",
]


NEGATIVE_KEYWORDS = [
    "fined",
    "court",
    "lawsuit",
    "breach",
    "investigation",
    "loss",
    "losses",
    "job cuts",
    "fraud",
    "risk",
    "warning",
    "crackdown",
    "penalty",
    "exfiltrated",
    "hacker",
    "attack",
    "threat",
]


NEUTRAL_POLICY_KEYWORDS = [
    "policy",
    "budget",
    "tax",
    "levy",
    "regulation",
    "government",
    "inquiry",
    "reform",
]


def safe_list(value) -> List:
    if isinstance(value, list):
        return value

    if value is None:
        return []

    return [value]


def detect_market_sentiment(article: Dict) -> str:
    title = str(article.get("title", "")).lower()
    text = str(article.get("cleaned_text", "")).lower()
    event_type = str(article.get("event_type", ""))

    combined = f"{title} {text}"

    positive_hits = sum(1 for word in POSITIVE_KEYWORDS if word in combined)
    negative_hits = sum(1 for word in NEGATIVE_KEYWORDS if word in combined)
    neutral_hits = sum(1 for word in NEUTRAL_POLICY_KEYWORDS if word in combined)

    if event_type == "Policy / Economy":
        return "neutral"

    if event_type == "Regulation / Legal":
        if negative_hits >= 2:
            return "negative"
        return "neutral"

    if negative_hits >= positive_hits + 2:
        return "negative"

    if event_type in POSITIVE_EVENT_TYPES and positive_hits >= 1 and negative_hits == 0:
        return "positive"

    if positive_hits >= negative_hits + 2:
        return "positive"

    if neutral_hits > 0:
        return "neutral"

    return "neutral"


def calculate_relevance_score(article: Dict) -> int:
    score = 1

    event_type = str(article.get("event_type", ""))
    primary_company = str(article.get("primary_company", "")).strip()

    confidence_score = int(float(article.get("confidence_score", 0) or 0))
    suitability_score = int(float(article.get("suitability_score", 0) or 0))

    money_amounts = safe_list(article.get("money_amounts", []))
    organisations = safe_list(article.get("organisations", []))

    if event_type in {"Funding", "Acquisition", "Partnership", "Expansion"}:
        score += 2
    elif event_type in {"Technology / AI", "Policy / Economy", "Regulation / Legal"}:
        score += 1

    if primary_company:
        score += 1

    if confidence_score >= 80:
        score += 1

    if suitability_score >= 40:
        score += 1

    if money_amounts:
        score += 1

    if len(organisations) >= 2:
        score += 1

    if event_type == "General Business Update":
        score -= 1

    if confidence_score < 60:
        score -= 1

    if not primary_company:
        score -= 1

    return max(1, min(score, 5))