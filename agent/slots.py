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
    "nightgowns",
    "undershirts",
    "sweatshirts",
    "sweatpants",
    "tracksuits",
    "raincoats",
    "sneakers",
    "leggings",
    "handbags",
    "wallets",
    "blouses",
    "jackets",
    "dresses",
    "hoodies",
    "sweaters",
    "bikinis",
    "anoraks",
    "loafers",
    "jerseys",
    "tunics",
    "briefs",
    "panties",
    "shirts",
    "shorts",
    "gloves",
    "socks",
    "jeans",
    "boots",
    "shoes",
    "pants",
    "robes",
    "tanks",
    "belts",
    "bras",
    "hats",
    "caps",
    "wallet",
    "blouse",
    "jacket",
    "dress",
    "hoodie",
    "sweater",
    "bikini",
    "jersey",
    "tunic",
    "shirt",
    "glove",
    "sock",
    "robe",
    "tank",
    "belt",
    "bra",
    "hat",
    "cap",
)

_BARE_SIZE_TOKENS = ("xs", "xl", "xxl")
_PREFIX_SIZE_TOKENS = ("xs", "s", "m", "l", "xl", "xxl")

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
_SIZE_PREFIX_RE = re.compile(
    r"\bsize\s+(" + "|".join(_PREFIX_SIZE_TOKENS) + r"|\d+)\b",
    re.IGNORECASE,
)
_SIZE_BARE_RE = re.compile(
    r"\b(" + "|".join(_BARE_SIZE_TOKENS) + r")\b",
    re.IGNORECASE,
)
_BUDGET_RE = re.compile(
    r"(?:under\s+\$?\s*(\d+(?:\.\d+)?)|\$\s*(\d+(?:\.\d+)?))",
    re.IGNORECASE,
)
_BRAND_BY_RE = re.compile(r"\bby\s+([A-Za-z][\w-]*)", re.IGNORECASE)


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

    size_prefix = _SIZE_PREFIX_RE.search(text)
    if size_prefix:
        slots["size"] = size_prefix.group(1).lower()
    else:
        size_bare = _SIZE_BARE_RE.search(text)
        if size_bare:
            slots["size"] = size_bare.group(1).lower()

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

    # Drop anything outside the allowed attribute set (defensive).
    return {k: v for k, v in slots.items() if k in ALLOWED_ATTRIBUTES}


WEAK_FILL = frozenset({"style", "feature", "use_case", "other"})
HARD_CONSTRAINTS = frozenset({"category", "brand", "budget", "size", "material", "color"})
_MATTERS_RE = re.compile(r"what matters is:\s+(.+)", re.IGNORECASE)
_NO_PREF_RE = re.compile(r"don'?t have (an additional |a )?preference", re.IGNORECASE)


def preference_snippet(message: str) -> str | None:
    if not message or not message.strip():
        return None
    if _NO_PREF_RE.search(message):
        return None
    match = _MATTERS_RE.search(message)
    text = match.group(1) if match else message
    text = re.sub(r"\s+", " ", text).strip(" .;")
    tokens = [token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 1][:4]
    if not tokens:
        return None
    return " ".join(tokens)


def _blob(product: dict) -> str:
    parts: list[str] = []
    for field in ("title", "features", "details", "description", "categories"):
        value = product.get(field)
        if isinstance(value, dict):
            parts.extend(f"{key} {item}" for key, item in value.items())
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif value not in (None, ""):
            parts.append(str(value))
    return " ".join(parts)


def visible_attrs(product: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    blob = _blob(product)
    color = _COLOR_RE.search(blob)
    if color:
        out["color"] = color.group(1).lower()
    material = _MATERIAL_RE.search(blob)
    if material:
        out["material"] = material.group(1).lower()
    store = product.get("store")
    if store:
        out["brand"] = str(store)
    price = product.get("price")
    if price not in (None, ""):
        try:
            amount = float(price)
        except (TypeError, ValueError):
            amount = None
        if amount is not None:
            if amount < 25:
                out["budget"] = "low"
            elif amount < 75:
                out["budget"] = "mid"
            else:
                out["budget"] = "high"
    return out


def pool_attrs_from_products(products: list[dict]) -> dict[str, set[str]]:
    pooled: dict[str, set[str]] = {}
    for product in products:
        for key, value in visible_attrs(product).items():
            pooled.setdefault(key, set()).add(value)
    return pooled
