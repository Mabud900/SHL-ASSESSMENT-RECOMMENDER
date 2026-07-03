import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


CATALOG_PATH = Path(__file__).parent / "data" / "catalog.json"

KEY_TO_TYPE = {
    "Ability & Aptitude": "A",
    "Assessment Exercises": "E",
    "Biodata & Situational Judgment": "B",
    "Competencies": "C",
    "Development & 360": "D",
    "Knowledge & Skills": "K",
    "Personality & Behavior": "P",
    "Simulations": "S",
}


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("&", " and ")
    text = text.replace("â€“", "-").replace("–", "-").replace("—", "-")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def test_type_for(item: dict[str, Any]) -> str:
    keys = item.get("keys") or []
    types = [KEY_TO_TYPE[key] for key in keys if key in KEY_TO_TYPE]
    return ",".join(dict.fromkeys(types)) or "K"


def public_item(item: dict[str, Any]) -> dict[str, str]:
    return {
        "name": item["name"],
        "url": item["link"],
        "test_type": test_type_for(item),
    }


@lru_cache(maxsize=1)
def load_catalog() -> list[dict[str, Any]]:
    with CATALOG_PATH.open("r", encoding="utf-8") as f:
        # The scraped SHL catalog can contain raw control characters inside
        # long text fields. strict=False keeps loading tolerant while still
        # preserving the JSON structure we need for recommendations.
        raw = json.loads(f.read(), strict=False)

    items: list[dict[str, Any]] = []
    for item in raw:
        if item.get("status") != "ok":
            continue
        item = dict(item)
        searchable_parts = [
            item.get("name", ""),
            item.get("description", ""),
            " ".join(item.get("keys") or []),
            " ".join(item.get("job_levels") or []),
            " ".join(item.get("languages") or []),
        ]
        item["_search"] = normalize(" ".join(searchable_parts))
        item["_name_norm"] = normalize(item.get("name", ""))
        item["_test_type"] = test_type_for(item)
        items.append(item)
    return items


@lru_cache(maxsize=1)
def catalog_by_name() -> dict[str, dict[str, Any]]:
    return {item["_name_norm"]: item for item in load_catalog()}


def find_by_name(name: str) -> dict[str, Any] | None:
    target = normalize(name)
    by_name = catalog_by_name()
    if target in by_name:
        return by_name[target]
    for item in load_catalog():
        item_name = item["_name_norm"]
        if target in item_name or item_name in target:
            return item
    return None


def names_to_recommendations(names: list[str]) -> list[dict[str, str]]:
    seen: set[str] = set()
    recs: list[dict[str, str]] = []
    for name in names:
        item = find_by_name(name)
        if not item:
            continue
        if item["link"] in seen:
            continue
        seen.add(item["link"])
        recs.append(public_item(item))
        if len(recs) == 10:
            break
    return recs
