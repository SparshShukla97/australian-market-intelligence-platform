import re
from nlp.gliner_extractor import extract_with_gliner
from typing import Dict, List

import spacy


nlp = spacy.load("en_core_web_sm")


EVENT_KEYWORDS = {
    "Funding": [
        "raised", "raises", "funding", "series a", "series b",
        "seed round", "investment", "invested", "backed",
        "grant", "capital raise", "banked",
    ],
    "Acquisition": [
        "acquired", "acquires", "acquisition", "merger", "merged",
        "takeover", "bought", "buyout", "sold", "sale",
    ],
    "Partnership": [
        "partnership", "partnered", "collaboration", "agreement",
        "signed a deal", "deal with", "joint venture",
    ],
    "Expansion": [
        "expansion", "expand", "expanded", "launch", "launched",
        "opened", "rollout", "build", "construction", "new facility",
        "scale", "growth",
    ],
    "Regulation / Legal": [
        "court", "lawsuit", "legal", "regulator", "watchdog",
        "fined", "fine", "investigation", "breach", "federal court",
    ],
    "Policy / Economy": [
        "policy", "tax", "levy", "budget", "inflation",
        "government", "reform", "regulation", "interest rate",
    ],
    "Technology / AI": [
        "ai", "artificial intelligence", "machine learning",
        "cloud", "cybersecurity", "data centre", "automation",
        "software", "platform", "digital",
    ],
}


EVENT_PRIORITY = [
    "Funding",
    "Acquisition",
    "Regulation / Legal",
    "Partnership",
    "Expansion",
    "Policy / Economy",
    "Technology / AI",
]


MONEY_PATTERN = re.compile(
    r"(?:A\$|US\$|\$|AUD\s?|USD\s?)\s?\d+(?:\.\d+)?\s?"
    r"(?:million|billion|m|bn|k)",
    re.IGNORECASE,
)


GENERIC_ORG_NOISE = {
    "inside retail",
    "startup daily",
    "it news",
    "innovationaus",
    "renew economy",
    "pv magazine australia",
    "abc news",
    "sbs news australia",
    "the australia institute",
    "sku",
    "esg",
    "ipo",
    "ceo",
    "cfo",
    "coo",
    "cto",
    "ai",
    "agency",
    "big tech",
    "cyber",
    "technology",
    "intelligence",
    "trust",
    "platform",
    "system",
    "group",
    "company",
    "firm",
    "enterprise",
}

PERSON_NOISE_WORDS = [
    "retail",
    "fashion",
    "ladies",
    "bay",
    "group",
    "capital",
    "funds",
    "brands",
    "mall",
    "centre",
    "center",
    "road",
    "street",
    "holdings",
    "furniture",
    "supermarket",
]


ORG_SUFFIX_WORDS = [
    "group",
    "capital",
    "funds",
    "brands",
    "bank",
    "university",
    "partners",
    "ventures",
    "holdings",
    "limited",
    "ltd",
    "inc",
    "corp",
    "corporation",
    "foundation",
    "council",
    "commission",
    "authority",
    "department",
    "agency",
]

BUSINESS_CONTEXT_WORDS = [
    "fined",
    "faces",
    "court",
    "tax",
    "promotion",
    "sales",
    "revenue",
    "turnaround",
    "brand",
    "retail",
    "company",
    "business",
    "sold",
    "acquired",
    "merger",
]


def clean_entity_text(entity: str) -> str:
    entity = entity.strip()
    entity = entity.replace("’s", "").replace("'s", "")
    entity = re.sub(r"\s+", " ", entity)
    entity = entity.strip(" ,.-:;()[]{}\"'")
    return entity


def deduplicate(items: List[str]) -> List[str]:
    cleaned_items = []
    seen = set()

    for item in items:
        item = clean_entity_text(item)

        if not item:
            continue

        key = item.lower()

        if key not in seen:
            seen.add(key)
            cleaned_items.append(item)

    return cleaned_items


def looks_like_money(entity: str) -> bool:
    return bool(
        re.fullmatch(
            r"(?:A\$|US\$|\$|AUD\s?|USD\s?)?\s?\d+(?:\.\d+)?\s?"
            r"(?:million|billion|m|bn|k)?",
            entity.strip(),
            flags=re.IGNORECASE,
        )
    )


def looks_like_org(entity: str) -> bool:
    cleaned = entity.lower()

    if any(word in cleaned for word in ORG_SUFFIX_WORDS):
        return True

    if entity.isupper() and len(entity) > 2:
        return True

    return False

def should_move_person_to_org(entity: str, title: str) -> bool:
    title_lower = title.lower()
    entity_lower = entity.lower()

    if entity_lower not in title_lower:
        return False

    if not any(word in title_lower for word in BUSINESS_CONTEXT_WORDS):
        return False

    if title_lower.startswith(("who", "why", "how")):
        return False

    return True


def is_valid_organisation(entity: str) -> bool:
    cleaned = entity.lower().strip()

    if not cleaned:
        return False

    if cleaned in GENERIC_ORG_NOISE:
        return False

    if len(cleaned) <= 2:
        return False

    if looks_like_money(cleaned):
        return False

    if cleaned.endswith("&"):
        return False

    if cleaned in {"agency", "firm", "group", "company"}:
        return False

    words = cleaned.split()

    if len(words) == 1:
        if cleaned in {
            "agency",
            "cyber",
            "technology",
            "trust",
            "platform",
            "system",
            "firm",
            "company",
        }:
            return False

    return True


def is_valid_person(entity: str) -> bool:
    cleaned = entity.lower().strip()

    if not cleaned:
        return False

    if len(entity.split()) < 2:
        return False

    if cleaned in GENERIC_ORG_NOISE:
        return False

    if looks_like_money(entity):
        return False

    if any(word in cleaned for word in PERSON_NOISE_WORDS):
        return False

    if looks_like_org(entity):
        return False

    return True


def extract_spacy_entities(text: str, title: str = "") -> Dict[str, List[str]]:
    doc = nlp(text)

    organisations = []
    people = []
    locations = []

    for ent in doc.ents:
        entity = clean_entity_text(ent.text)

        if not entity:
            continue

        if ent.label_ == "ORG":
            if is_valid_organisation(entity):
                organisations.append(entity)

        elif ent.label_ == "PERSON":
            if should_move_person_to_org(entity, title) and is_valid_organisation(entity):
                organisations.append(entity)
            elif looks_like_org(entity) and is_valid_organisation(entity):
                organisations.append(entity)
            elif is_valid_person(entity):
                people.append(entity)

        elif ent.label_ in ["GPE", "LOC"]:
            if not looks_like_money(entity):
                locations.append(entity)

    return {
        "organisations": deduplicate(organisations),
        "people": deduplicate(people),
        "locations": deduplicate(locations),
    }


def extract_money(text: str) -> List[str]:
    matches = MONEY_PATTERN.findall(text)
    return deduplicate(matches)


def detect_event_type(title: str, text: str) -> str:
    combined = f"{title} {text}".lower()
    scores = {}

    for event_type, keywords in EVENT_KEYWORDS.items():
        count = sum(1 for keyword in keywords if keyword in combined)
        if count > 0:
            scores[event_type] = count

    if not scores:
        return "General Business Update"

    best_score = max(scores.values())
    top_events = [event for event, score in scores.items() if score == best_score]

    for event in EVENT_PRIORITY:
        if event in top_events:
            return event

    return top_events[0]


LOW_PRIORITY_ORG_TERMS = [
    "court",
    "federal court",
    "supreme court",
    "commission",
    "authority",
    "regulator",
    "department",
    "government",
    "police",
    "review",
    "inquiry",
]


def is_low_priority_org(org: str) -> bool:
    org_lower = org.lower()
    return any(term in org_lower for term in LOW_PRIORITY_ORG_TERMS)


def choose_primary_company(title: str, organisations: List[str]) -> str:
    if not organisations:
        return ""

    title_lower = title.lower()

    title_matches = [
        org for org in organisations
        if org.lower() in title_lower and not is_low_priority_org(org)
    ]

    if title_matches:
        return title_matches[0]

    non_low_priority_orgs = [
        org for org in organisations
        if not is_low_priority_org(org)
    ]

    if non_low_priority_orgs:
        return non_low_priority_orgs[0]

    return organisations[0]


def calculate_confidence(
    primary_company: str,
    organisations: List[str],
    money_amounts: List[str],
    event_type: str,
    cleaned_text: str,
) -> int:
    confidence = 0

    if primary_company:
        confidence += 30

    if organisations:
        confidence += 15

    if money_amounts:
        confidence += 20

    if event_type != "General Business Update":
        confidence += 20

    if len(cleaned_text) > 500:
        confidence += 10

    if len(organisations) > 10:
        confidence -= 15

    if event_type == "General Business Update":
        confidence -= 15

    return max(0, min(confidence, 100))

def is_suspicious_primary_company(primary_company: str) -> bool:
    if not primary_company:
        return True
    cleaned = primary_company.strip()

    if len(cleaned) <= 3:
        return True
    suspicious_terms = [
        "strengthens",
        "launches",
        "announces",
        "expands",
        "boosts",
        "grows",
    ]
    if any(term in cleaned.lower() for term in suspicious_terms):
        return True
    if cleaned.isupper() and len(cleaned) <= 5:
        return True

    return False


def extract_article_intelligence(article: Dict) -> Dict:
    title = article.get("title", "")
    cleaned_text = article.get("cleaned_text", "")
    combined_text = f"{title}. {cleaned_text}"

    entity_results = extract_spacy_entities(
       combined_text,
       title=title,
    )

    gliner_results = extract_with_gliner(
       title=title,
       cleaned_text=cleaned_text,
    )

    money_amounts = extract_money(combined_text)
    event_type = detect_event_type(title, cleaned_text)

    combined_organisations = list(
       dict.fromkeys(
        entity_results["organisations"] +
        gliner_results["gliner_companies"] +
        gliner_results["gliner_government_organisations"]
      )
    )

    combined_people = list(
      dict.fromkeys(
        entity_results["people"] +
        gliner_results["gliner_people"]
      )
    )

    combined_locations = list(
      dict.fromkeys(
        entity_results["locations"] +
        gliner_results["gliner_locations"]
      )
    )

    combined_money = list(
      dict.fromkeys(
        money_amounts +
        gliner_results["gliner_money_amounts"]
      )
    )

    primary_company = choose_primary_company(
        title=title,
        organisations=combined_organisations,
    )

    confidence_score = calculate_confidence(
        primary_company=primary_company,
        organisations=combined_organisations,
        money_amounts=combined_money,
        event_type=event_type,
        cleaned_text=cleaned_text,
    )

    needs_gpt_fallback = (
        confidence_score < 70
        or is_suspicious_primary_company(primary_company)
    )

    return {
        "primary_company": primary_company,
        "organisations": combined_organisations,
        "people": combined_people,
        "locations": combined_locations,
        "money_amounts": combined_money,
        "event_type": event_type,
        "confidence_score": confidence_score,
        "needs_gpt_fallback": needs_gpt_fallback,
    }