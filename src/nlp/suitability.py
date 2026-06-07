from typing import Dict, List


GLOBAL_POSITIVE_SIGNALS = [
    "raised", "raise", "funding", "investment", "invest", "venture", "capital",
    "series a", "series b", "seed round", "grant", "subsidy",
    "acquisition", "acquire", "merger", "partnership", "contract",
    "deal", "agreement", "collaboration", "signed",
    "launch", "expand", "expansion", "open", "build", "facility",
    "rollout", "infrastructure", "project", "construction",
    "government", "regulation", "policy", "approval", "planning",
    "fine", "fined", "court", "lawsuit", "legal", "tax", "levy",
]

CATEGORY_SIGNALS = {
    "Technology": [
        "ai", "artificial intelligence", "machine learning", "cloud",
        "data centre", "cybersecurity", "cyber attack", "data breach",
        "platform", "automation", "semiconductor", "chip", "software",
        "digital", "enterprise", "analytics", "startup", "tech",
        "big tech", "openai", "microsoft", "aws", "google",
    ],
    "Funding": [
        "raised", "funding", "investment", "investor", "venture capital",
        "seed", "series a", "series b", "backed", "round", "valuation",
        "capital raise", "startup", "fund", "banked",
    ],
    "Energy": [
        "energy", "solar", "battery", "renewable", "grid", "wind",
        "hydrogen", "gas", "electricity", "power", "transmission",
        "storage", "emissions", "clean energy", "green energy",
        "bess", "ev", "electrification",
    ],
    "Retail": [
        "retail", "store", "consumer", "ecommerce", "shopping",
        "brand", "customer", "sales", "supermarket", "woolworths",
        "coles", "ceo", "appointment", "online retail", "discounting",
        "promotion", "advertising", "product sales", "turnaround",
        "private equity", "federal court", "fined",
    ],
    "Property": [
        "property", "housing", "real estate", "rental", "rent",
        "construction", "development", "building approvals",
        "home prices", "house prices", "market", "affordability",
        "planning", "domain data", "rba", "rate hike",
        "dwelling", "apartments", "housing supply",
    ],
    "Policy_Economy": [
        "tax", "budget", "inflation", "economy", "economic",
        "policy", "government", "regulation", "fuel", "gas export",
        "ndis", "wage", "recession", "trade", "productivity",
        "cost of living", "treasury", "migration", "housing crisis",
        "interest rate", "exports", "supply chain", "super-rich",
        "gas tax", "fuel prices",
    ],
}

EVENT_SIGNALS = [
    "raised", "funding", "investment", "acquisition", "merger",
    "partnership", "contract", "deal", "launch", "expansion",
    "approval", "regulation", "court", "appoints", "names",
    "spend", "grant", "build", "rollout", "fined", "tax",
    "levy", "warns", "announces", "targets",
]

HARD_REJECT_SIGNALS = [
    "anzac", "sports", "match", "artist", "music", "celebrity",
    "recipe", "murder", "crime", "true crime", "weather",
    "personal story", "war memorial", "football", "swimming",
]

NEGATIVE_SIGNALS = [
    "opinion", "commentary", "editorial", "explainer",
    "what do you think", "let me know", "in the comments",
    "newsletter", "subscribe", "how to", "tips", "guide",
    "review", "podcast", "myth", "narrative", "big green lies",
    "ways to make money", "rich people", "wealth partner",
    "feng shui", "ancient wisdom", "booming property market",
]

SOURCE_WEIGHTS = {
    "IT News": 4,
    "InnovationAus": 3,
    "RenewEconomy": 3,
    "PV Magazine Australia": 3,
    "Inside Retail": 3,
    "The Property Tribune": 2,
    "Startup Daily": 0,
    "SBS News Australia": -1,
    "The Australia Institute": -2,
    "Property Update": -2,
    "ABC News": -2,
}


def find_hits(words: List[str], text: str) -> List[str]:
    return [word for word in words if word in text]


def evaluate_article_suitability(
    title: str,
    source: str,
    cleaned_text: str,
    category: str = "",
) -> Dict:
    combined = f"{title} {cleaned_text}".lower()
    title_lower = title.lower()

    hard_reject_hits = find_hits(HARD_REJECT_SIGNALS, combined)

    if hard_reject_hits:
        return {
            "is_suitable": False,
            "suitability_level": "rejected",
            "suitability_score": 0,
            "global_positive_hits": [],
            "category_hits": [],
            "event_hits": [],
            "negative_hits": [],
            "hard_reject_hits": hard_reject_hits,
        }

    global_positive_hits = find_hits(GLOBAL_POSITIVE_SIGNALS, combined)
    category_hits = find_hits(CATEGORY_SIGNALS.get(category, []), combined)
    event_hits = find_hits(EVENT_SIGNALS, combined)
    negative_hits = find_hits(NEGATIVE_SIGNALS, combined)

    score = 0
    score += len(global_positive_hits) * 2
    score += len(category_hits) * 3
    score += len(event_hits) * 3
    score -= len(negative_hits) * 5
    score += SOURCE_WEIGHTS.get(source, 0)

    if len(category_hits) == 0:
        score -= 8

    if len(event_hits) == 0:
        score -= 6

    if title_lower.startswith(("how", "why", "can", "what", "is")):
        score -= 5

    if "?" in title:
        score -= 4

    if len(cleaned_text) < 300:
        score -= 3

    if negative_hits and len(event_hits) < 2:
        score -= 6

    if category == "Property":
        property_noise_phrases = [
         "feng shui",
         "avoid the herd",
         "good place to invest",
         "property deception",
         "awards",
         "gala",
         "grand final",
         "wealth",
         "property investors",
         "property insiders",
        ]

        if any(phrase in title_lower for phrase in property_noise_phrases):
         score -= 18

        if negative_hits:
         score -= 8
    
    if category == "Retail":
        retail_noise_phrases = [
        "fashion",
        "luxury",
        "campaign",
        "adidas",
        "style",
        "collabs",
        "marathon",
        "beauty",
        ]

        if any(phrase in title_lower for phrase in retail_noise_phrases):
         score -= 16

    if category == "Policy_Economy":
        if any(word in combined for word in ["trump", "iran", "war", "military"]) and not any(
            word in combined for word in ["inflation", "fuel", "tax", "budget", "economy", "trade"]
        ):
            score -= 8

    if score >= 25:
        suitability_level = "high"
        is_suitable = True
    elif score >= 18:
        suitability_level = "medium"
        is_suitable = True
    else:
        suitability_level = "low"
        is_suitable = False

    return {
        "is_suitable": is_suitable,
        "suitability_level": suitability_level,
        "suitability_score": score,
        "global_positive_hits": global_positive_hits,
        "category_hits": category_hits,
        "event_hits": event_hits,
        "negative_hits": negative_hits,
        "hard_reject_hits": hard_reject_hits,
    }