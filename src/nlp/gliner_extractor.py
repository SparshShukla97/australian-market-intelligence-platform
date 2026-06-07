from typing import Dict, List

from gliner import GLiNER


MODEL_NAME = "urchade/gliner_medium-v2.1"

LABELS = [
    "company",
    "person",
    "location",
    "government organization",
    "money",
]

MIN_SCORE = 0.65
MAX_TEXT_LENGTH = 2000

_model = None


def get_gliner_model():
    global _model

    if _model is None:
        _model = GLiNER.from_pretrained(MODEL_NAME)

    return _model


def prepare_text(title: str, cleaned_text: str) -> str:
    text = f"{title}. {cleaned_text}"
    text = text.strip()

    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]

    return text


def deduplicate_entities(entities: List[Dict]) -> List[Dict]:
    seen = set()
    cleaned_entities = []

    for entity in entities:
        text = entity.get("text", "").strip()
        label = entity.get("label", "").strip()
        score = float(entity.get("score", 0))

        if not text or not label:
            continue

        key = (text.lower(), label.lower())

        if key not in seen:
            seen.add(key)
            cleaned_entities.append(
                {
                    "text": text,
                    "label": label,
                    "score": round(score, 3),
                }
            )

    return cleaned_entities


def extract_with_gliner(title: str, cleaned_text: str) -> Dict:
    model = get_gliner_model()
    text = prepare_text(title, cleaned_text)

    raw_entities = model.predict_entities(
        text,
        labels=LABELS,
    )

    filtered_entities = [
        entity for entity in raw_entities
        if float(entity.get("score", 0)) >= MIN_SCORE
    ]

    entities = deduplicate_entities(filtered_entities)

    companies = []
    people = []
    locations = []
    government_organisations = []
    money_amounts = []

    for entity in entities:
        label = entity["label"]
        text_value = entity["text"]

        if label == "company":
            companies.append(text_value)
        elif label == "person":
            people.append(text_value)
        elif label == "location":
            locations.append(text_value)
        elif label == "government organization":
            government_organisations.append(text_value)
        elif label == "money":
            money_amounts.append(text_value)

    return {
        "gliner_companies": companies,
        "gliner_people": people,
        "gliner_locations": locations,
        "gliner_government_organisations": government_organisations,
        "gliner_money_amounts": money_amounts,
        "gliner_entities": entities,
    }