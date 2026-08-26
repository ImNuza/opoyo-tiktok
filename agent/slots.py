from __future__ import annotations

import re

from agent.state import ALLOWED_ATTRIBUTES

_COLOR_WORDS = (
    "black",
    "white",
    "blue",
    "red",
    "pink",
    "green",
    "brown",
    "gray",
    "grey",
    "purple",
    "yellow",
    "orange",
)

_MATERIAL_WORDS = (
    "cotton",
    "polyester",
    "nylon",
    "leather",
    "wool",
    "spandex",
    "silk",
    "rayon",
    "fabric",
)

_CATEGORY_WORDS = (
    "shoes",
    "boots",
    "dress",
    "jacket",
    "shirt",
    "hat",
    "jeans",
    "sneakers",
)

_SIZE_TOKENS = ("xs", "s", "m", "l", "xl", "xxl")

_COLOR_RE = re.compile(
    r"\b(" + "|".join(_COLOR_WORDS) + r")\b",
    re.IGNORECASE,
)
_MATERIAL_RE = re.compile(
    r"\b(" + "|".join(_MATERIAL_WORDS) + r")\b",
    re.IGNORECASE,
)
_CATEGORY_RE = re.compile(
    r"\b(" + "|".join(_CATEGORY_WORDS) + r")\b",
    re.IGNORECASE,
)
_SIZE_TOKEN_RE = re.compile(
    r"\b(" + "|".join(_SIZE_TOKENS) + r")\b",
    re.IGNORECASE,
)
_SIZE_NUMBER_RE = re.compile(r"\bsize\s+(\d+)\b", re.IGNORECASE)
_BUDGET_RE = re.compile(
    r"(?:under\s+\$?\s*(\d+(?:\.\d+)?)|\$\s*(\d+(?:\.\d+)?))",
    re.IGNORECASE,
)
_BRAND_BY_RE = re.compile(r"\bby\s+([A-Za-z][\w-]*)", re.IGNORECASE)

_RESERVED_LOWER = {w.lower() for w in _COLOR_WORDS + _MATERIAL_WORDS}


def parse_slots(message: str, profile: dict | None = None) -> dict[str, str]:
    if not message or not message.strip():
        return {}

    slots: dict[str, str] = {}
    text = message

    color_match = _COLOR_RE.search(text)
    if color_match:
        slots["color"] = color_match.group(1).lower()

    material_match = _MATERIAL_RE.search(text)
    if material_match:
        slots["material"] = material_match.group(1).lower()

    category_match = _CATEGORY_RE.search(text)
    if category_match:
        slots["category"] = category_match.group(1).lower()

    size_number = _SIZE_NUMBER_RE.search(text)
    if size_number:
        slots["size"] = size_number.group(1)
    else:
        size_token = _SIZE_TOKEN_RE.search(text)
        if size_token:
            slots["size"] = size_token.group(1).lower()

    budget_match = _BUDGET_RE.search(text)
    if budget_match:
        amount = budget_match.group(1) or budget_match.group(2)
        if amount is not None:
            if "." in amount:
                slots["budget"] = amount.rstrip("0").rstrip(".")
            else:
                slots["budget"] = amount

    brand_by = _BRAND_BY_RE.search(text)
    if brand_by:
        slots["brand"] = brand_by.group(1)
    elif profile:
        tags = profile.get("preference_tags") or []
        for tag in tags:
            if not isinstance(tag, str):
                continue
            if tag.lower() in _RESERVED_LOWER:
                continue
            slots["brand"] = tag
            break

    # Drop anything outside the allowed attribute set (defensive).
    return {k: v for k, v in slots.items() if k in ALLOWED_ATTRIBUTES}
