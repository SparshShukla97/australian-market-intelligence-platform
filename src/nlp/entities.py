from typing import Dict, List, Set
import re
import spacy

# Load spaCy model once
nlp = spacy.load("en_core_web_sm")

# Important business/government organization patterns
BUSINESS_ORG_PATTERNS = [
    r"\bfederal government\b",
    r"\bstate government\b",
    r"\bnsw government\b",
    r"\bvictorian government\b",
    r"\bqueensland government\b",
    r"\baustralian government\b",
    r"\bnational reconstruction fund\b",
    r"\bdepartment of defence\b",
    r"\btreasury\b",
    r"\baccc\b",
    r"\bapra\b",
    r"\basic\b",
]

# Weak/incorrect org candidates for this project
ORG_BLACKLIST = {
    "mw", "ai", "modern ai", "gelsinger", "pro forma",
    "s4", "s4 sydney", "wolverine", "azure"
}

# Weak/incorrect person candidates
PERSON_BLACKLIST = {
    "ai", "syenta", "playground global", "salus ventures", "jelix ventures",
    "blackbird jelix", "brindabella capital", "wollemi capital", "sginnovate",
    "oif", "localized electrochemical manufacturing", "lem", "s4", "s4 sydney",
    "pro forma", "la caisse", "mw", "meta cto", "humanitix as head of"
}

# Weak/incorrect location candidates
LOCATION_BLACKLIST = {
    "ai", "syenta", "nvidia", "playground global", "silicon valley vc",
    "mw", "gemini", "titan", "azure", "humanitix", "ticketek"
}

ROLE_WORDS = {
    "ceo", "cto", "cfo", "cofounder", "founder", "director", "chair",
    "head", "spokesperson", "manager", "minister"
}


def normalize_entity_text(value: str) -> str:
    """
    Light cleanup for extracted entity text.
    """
    if not value:
        return ""

    value = value.strip()
    value = re.sub(r"[’']s$", "", value)  # remove trailing possessive
    value = re.sub(r"^the\s+", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", " ", value)

    return value.strip(" ,.-:;\"'“”")


def deduplicate_preserve_order(items: List[str]) -> List[str]:
    """
    Remove duplicates while preserving order.
    """
    seen = set()
    result = []

    for item in items:
        cleaned = normalize_entity_text(item)
        lowered = cleaned.lower()

        if cleaned and lowered not in seen:
            seen.add(lowered)
            result.append(cleaned)

    return result


def extract_money_patterns(text: str) -> List[str]:
    """
    Extract only real currency-style amounts.

    Intentionally excludes:
    - percentages
    - plain numbers without currency
    """
    if not text:
        return []

    pattern = re.compile(
        r"""
        (?:
            US\$|A\$|AUD\s?|USD\s?|\$
        )
        \s?
        \d+(?:\.\d+)?
        \s?
        (?:million|billion|trillion|m|bn)?
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    matches = pattern.findall(text)
    return deduplicate_preserve_order(matches)


def extract_business_org_patterns(text: str) -> List[str]:
    """
    Regex-based extraction for government/business bodies.
    """
    if not text:
        return []

    found = []

    for pattern in BUSINESS_ORG_PATTERNS:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        found.extend(matches)

    return deduplicate_preserve_order(found)


def extract_title_org_candidates(title: str) -> List[str]:
    """
    Extract likely main organization candidates from title patterns.

    This helps title-led articles where the main company is obvious in the title
    but less cleanly captured in the body.
    """
    if not title:
        return []

    candidates = []

    # Example: "NEXTDC to raise..."
    m = re.match(r"^([A-Z][A-Za-z0-9&.\- ]{1,60})\s+(?:to|raises|joins|hits|takes|plans|prioritises)\b", title)
    if m:
        candidates.append(m.group(1).strip())

    # Example: "ANU spinout raises ..."
    m2 = re.match(r"^([A-Z][A-Za-z0-9&.\- ]{1,60})\s+spinout\b", title)
    if m2:
        candidates.append(m2.group(1).strip())

    # Example: "Wolverine star Hugh Jackman joins ticketing startup Humanitix ..."
    # Capture "... startup Humanitix"
    m3 = re.search(r"\bstartup\s+([A-Z][A-Za-z0-9&.\-]+)\b", title)
    if m3:
        candidates.append(m3.group(1).strip())

    return deduplicate_preserve_order(candidates)


def is_valid_org(value: str) -> bool:
    cleaned = normalize_entity_text(value)
    lowered = cleaned.lower()

    if not cleaned:
        return False

    if lowered in ORG_BLACKLIST:
        return False

    if len(cleaned) <= 2:
        return False

    # Filter role fragments that are not companies
    if any(word in lowered for word in ["head of", "spokesperson", "ceo and", "cto and"]):
        return False

    return True


def is_valid_person(value: str) -> bool:
    cleaned = normalize_entity_text(value)
    lowered = cleaned.lower()

    if not cleaned:
        return False

    if lowered in PERSON_BLACKLIST:
        return False

    # Drop obvious role fragments
    if any(role in lowered for role in ROLE_WORDS) and len(cleaned.split()) < 3:
        return False

    # Conservative rule: person should usually have 2+ words
    if len(cleaned.split()) < 2:
        return False

    return True


def is_valid_location(value: str, org_set: Set[str]) -> bool:
    cleaned = normalize_entity_text(value)
    lowered = cleaned.lower()

    if not cleaned:
        return False

    if lowered in LOCATION_BLACKLIST:
        return False

    # If something is already a strong organization candidate, do not keep it as a location
    if lowered in org_set:
        return False

    return True


def extract_entities_from_text(text: str, title: str = "") -> Dict[str, List[str]]:
    """
    Extract candidate entities from article title + cleaned text.

    Returns grouped candidates:
    - organizations
    - people
    - locations
    - money

    This is still a candidate extraction stage, not final ranking.
    """
    combined_text = f"{title}. {text}".strip()

    if not combined_text:
        return {
            "organizations": [],
            "people": [],
            "locations": [],
            "money": [],
        }

    doc = nlp(combined_text)

    organizations = []
    people = []
    locations = []
    money = []

    # First pass: collect raw candidates
    for ent in doc.ents:
        value = ent.text.strip()
        label = ent.label_

        if label == "ORG" and is_valid_org(value):
            organizations.append(value)

        elif label == "PERSON" and is_valid_person(value):
            people.append(value)

        elif label == "MONEY":
            # Keep only money values with a currency symbol/word
            if re.search(r"(US\$|A\$|AUD|USD|\$)", value, flags=re.IGNORECASE):
                money.append(value)

        elif label in {"GPE", "LOC"}:
            locations.append(value)

    # Add business-aware org patterns
    organizations.extend(extract_business_org_patterns(combined_text))

    # Add title-aware org candidates
    organizations.extend(extract_title_org_candidates(title))

    # Add regex-based money extraction
    money.extend(extract_money_patterns(combined_text))

    # Clean/deduplicate organizations first so we can use them to filter locations
    organizations = deduplicate_preserve_order(organizations)
    org_set = {org.lower() for org in organizations}

    # Re-filter locations using org knowledge
    filtered_locations = []
    for loc in locations:
        if is_valid_location(loc, org_set):
            filtered_locations.append(loc)

    locations = deduplicate_preserve_order(filtered_locations)

    # Remove cross-field conflicts:
    # if something is an organization, do not keep it as person/location
    people = [
        p for p in deduplicate_preserve_order(people)
        if p.lower() not in org_set
    ]

    locations = [
        l for l in locations
        if l.lower() not in org_set
    ]

    money = deduplicate_preserve_order(money)

    return {
        "organizations": organizations,
        "people": people,
        "locations": locations,
        "money": money,
    }