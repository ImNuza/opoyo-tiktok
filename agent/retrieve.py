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

        if required_terms:
            and_part = " AND ".join(f'"{term}"' for term in required_terms)
            if extra_terms:
                or_part = " OR ".join(f'"{term}"' for term in extra_terms)
                expression = f"({and_part}) AND ({or_part})"
            else:
                expression = and_part
            hits = self._match(expression, limit)
            if hits:
                return hits
            hits = self._match(and_part, limit)
            if hits:
                return hits

        expression = " OR ".join(f'"{term}"' for term in query_terms)
        return self._match(expression, limit)
