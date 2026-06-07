import re
from typing import Dict

# These are obvious non-article phrases that commonly appear in scraped pages.
# We keep this list small and conservative so we do not accidentally remove
# meaningful article content.
NOISE_PATTERNS = [
    r"please login below to view content\.?",
    r"subscribe now\.?",
    r"read more\.?",
    r"listen to the podcast\.?",
    r"do you know more\?.*",
    r"contact .* via email\.?",
]


def normalize_whitespace(text: str) -> str:
    """
    Clean spacing issues without changing sentence meaning.

    This function:
    - replaces non-breaking spaces with normal spaces
    - reduces multiple spaces/tabs to a single space
    - reduces multiple blank lines
    - trims the text
    """
    if not text:
        return ""

    # Replace HTML-like non-breaking spaces with normal spaces
    text = text.replace("\xa0", " ")

    # Collapse repeated spaces or tabs into one space
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse multiple blank lines into a single newline
    text = re.sub(r"\n\s*\n+", "\n", text)

    return text.strip()


def remove_noise_patterns(text: str) -> str:
    """
    Remove obvious junk phrases such as login prompts, podcast prompts,
    or contact/footer phrases that are not part of the core article.
    """
    if not text:
        return ""

    cleaned = text

    for pattern in NOISE_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    return cleaned.strip()


def remove_duplicate_lines(text: str) -> str:
    """
    Remove repeated lines while preserving order.

    Why this matters:
    Some scraped pages contain the same line or paragraph multiple times.
    This function removes exact duplicates after normalizing spacing.
    """
    if not text:
        return ""

    # Split text into lines and ignore empty lines
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    seen = set()
    unique_lines = []

    for line in lines:
        # Normalize the line for duplicate checking
        normalized_line = re.sub(r"\s+", " ", line).strip().lower()

        if normalized_line not in seen:
            seen.add(normalized_line)
            unique_lines.append(line)

    return "\n".join(unique_lines)


def clean_article_text(text: str) -> str:
    """
    Main preprocessing function.

    Order matters:
    1. normalize spacing
    2. remove obvious noise
    3. remove repeated lines
    4. normalize spacing again

    This is intentionally conservative:
    it cleans text without making strong assumptions about article meaning.
    """
    if not text:
        return ""

    text = normalize_whitespace(text)
    text = remove_noise_patterns(text)
    text = remove_duplicate_lines(text)
    text = normalize_whitespace(text)

    return text


def build_preprocess_hints(title: str, text: str) -> Dict:
    """
    Create soft signals for later NLP stages.

    Important:
    This function does NOT decide final relevance.
    It only provides lightweight hints that later stages can use.

    Output includes:
    - business_signal_count: how many market/business/policy clues appear
    - noise_signal_count: how many low-value/junky clues appear
    - text_length: useful for sanity checking
    """
    combined = f"{title} {text}".lower()

    # Words often associated with meaningful business, investment,
    # policy, legal, or market intelligence signals.
    business_signals = [
        "investment", "funding", "raised", "expansion", "expand",
        "policy", "government", "regulation", "legal", "court",
        "economy", "tax", "inflation", "partnership", "acquisition",
        "merger", "construction", "facility", "energy", "retail",
        "technology", "data centre", "ai", "infrastructure"
    ]

    # Words often associated with weaker pages for this project,
    # such as podcast pages or generic advice/promotional content.
    noise_signals = [
        "podcast", "listen now", "subscribe", "tips", "how to", "advice"
    ]

    business_signal_count = sum(1 for word in business_signals if word in combined)
    noise_signal_count = sum(1 for word in noise_signals if word in combined)

    return {
        "business_signal_count": business_signal_count,
        "noise_signal_count": noise_signal_count,
        "text_length": len(text),
    }