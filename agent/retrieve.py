from __future__ import annotations

import re
import sqlite3

from agent.catalog import Catalog

TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "i", "im", "in", "is", "it", "me", "my", "of", "on", "or", "please", "some",
    "that", "the", "this", "to", "want", "with", "would", "you", "looking",
    "key", "requirement", "still", "exploring", "additional", "matters",
}

_FOOTWEAR = (
    "shoe", "shoes", "sneaker", "sneakers", "boot", "boots",
    "clog", "clogs", "mule", "mules", "loafer", "loafers",
    "sandal", "sandals", "heel", "heels",
)
_RAIN = ("rain", "raincoat", "raincoats", "rainboot", "rainboots", "waterproof")
_WALLET = ("wallet", "wallets", "billfold")


def _index_families(*families: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
    out: dict[str, tuple[str, ...]] = {}
    for family in families:
        for term in family:
            out[term] = family
    return out


HYPERNYMS: dict[str, tuple[str, ...]] = _index_families(_FOOTWEAR, _RAIN, _WALLET)


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(f"{key} {item}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


def _terms(text: str) -> list[str]:
    return [
        token.lower()
        for token in TOKEN_RE.findall(text)
        if len(token) > 1 and token.lower() not in STOPWORDS
    ]


def expand_terms(terms: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for term in terms:
        variants = HYPERNYMS.get(term, (term,))
        for variant in variants:
            if variant in seen:
                continue
            seen.add(variant)
            out.append(variant)
    return out


def _families_mentioned(terms: list[str]) -> list[tuple[str, ...]]:
    found: list[tuple[str, ...]] = []
    seen: set[int] = set()
    for term in terms:
        family = HYPERNYMS.get(term)
        if family is None:
            continue
        marker = id(family)
        if marker in seen:
            continue
        seen.add(marker)
        found.append(family)
    return found


def _quote_or(terms: list[str]) -> str:
    if not terms:
        return ""
    if len(terms) == 1:
        return f'"{terms[0]}"'
    inner = " OR ".join(f'"{term}"' for term in terms)
    return f"({inner})"


def build_query(message: str, slots: dict[str, str], extra: list[str] | None = None) -> str:
    parts: list[str] = []
    seen: set[str] = set()
    for value in slots.values():
        text = (value or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        parts.append(text)
    message_text = (message or "").strip()
    if message_text:
        key = message_text.lower()
        if key not in seen:
            parts.append(message_text)
    for item in extra or []:
        text = str(item or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        parts.append(text)
    return " ".join(parts)


class Retriever:
    def __init__(self, catalog: Catalog) -> None:
        self.catalog = catalog
        self.connection = sqlite3.connect(":memory:")
        self._build_index()

    def _build_index(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            "CREATE VIRTUAL TABLE products USING fts5("
            "parent_asin UNINDEXED, title, categories, features, details, store, description, "
            "tokenize='unicode61 remove_diacritics 2')"
        )
        batch: list[tuple[str, str, str, str, str, str, str]] = []
        for product in self.catalog.products.values():
            batch.append(
                (
                    str(product["parent_asin"]),
                    _text(product.get("title")),
                    _text(product.get("categories")),
                    _text(product.get("features")),
                    _text(product.get("details")),
                    _text(product.get("store")),
                    _text(product.get("description")),
                )
            )
            if len(batch) >= 1000:
                cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
                batch.clear()
        if batch:
            cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
        self.connection.commit()

    def _match(self, expression: str, limit: int) -> list[str]:
        if not expression:
            return []
        rows = self.connection.execute(
            "SELECT parent_asin FROM products WHERE products MATCH ? "
            "ORDER BY bm25(products, 0.0, 6.0, 4.0, 2.5, 2.5, 1.5, 1.0) LIMIT ?",
            (expression, limit),
        ).fetchall()
        results: list[str] = []
        for row in rows:
            parent_asin = str(row[0])
            if parent_asin in self.catalog.ids:
                results.append(parent_asin)
        return results

    def search(
        self,
        query: str,
        limit: int = 50,
        required: list[str] | None = None,
    ) -> list[str]:
        query_terms = list(dict.fromkeys(_terms(query)))[:40]
        required_terms: list[str] = []
        for value in required or []:
            for token in _terms(value):
                if token not in required_terms:
                    required_terms.append(token)
        required_terms = required_terms[:20]
        extra_terms = [term for term in query_terms if term not in required_terms][:20]
        families = _families_mentioned([*required_terms, *query_terms])

        and_groups: list[str] = []
        used_required_family: set[int] = set()
        for term in required_terms:
            family = HYPERNYMS.get(term)
            if family is not None:
                marker = id(family)
                if marker in used_required_family:
                    continue
                used_required_family.add(marker)
                and_groups.append(_quote_or(list(family)))
            else:
                and_groups.append(_quote_or([term]))
        for family in families:
            if id(family) in used_required_family:
                continue
            and_groups.append(_quote_or(list(family)))

        extra_non_family = [term for term in extra_terms if term not in HYPERNYMS]
        extra_clause = _quote_or(extra_non_family)

        if and_groups:
            and_part = " AND ".join(group for group in and_groups if group)
            if and_part and extra_clause:
                hits = self._match(f"({and_part}) AND {extra_clause}", limit)
                if hits:
                    return hits
            if and_part:
                hits = self._match(and_part, limit)
                if hits:
                    return hits

        expanded = expand_terms(query_terms)[:40]
        expression = " OR ".join(f'"{term}"' for term in expanded)
        return self._match(expression, limit)
