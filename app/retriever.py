from collections import Counter

from app.catalog import load_catalog, normalize, public_item


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "for",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "we",
    "with",
}


def tokenize(text: str) -> list[str]:
    return [tok for tok in normalize(text).split() if len(tok) > 1 and tok not in STOPWORDS]


def retrieve(query: str, limit: int = 10) -> list[dict[str, str]]:
    terms = tokenize(query)
    if not terms:
        return []
    counts = Counter(terms)
    scored: list[tuple[float, dict]] = []
    for item in load_catalog():
        score = 0.0
        search = item["_search"]
        name = item["_name_norm"]
        for term, weight in counts.items():
            if term in name.split():
                score += 8 * weight
            elif term in name:
                score += 5 * weight
            elif term in search:
                score += 1.5 * weight
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda row: (-row[0], row[1]["name"]))
    return [public_item(item) for _, item in scored[:limit]]

