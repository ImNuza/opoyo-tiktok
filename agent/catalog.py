from __future__ import annotations

import json
import re
from pathlib import Path


class CatalogError(Exception):
    pass


class Catalog:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if not self.path.is_file():
            raise CatalogError(f"catalog file is missing: {self.path}")
        products: dict[str, dict] = {}
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                products[str(row["parent_asin"])] = row
        if not products:
            raise CatalogError(f"catalog file is empty: {self.path}")
        self.products = products
        self.ids = set(products)
        self.category_lexicon = build_category_lexicon(products)

    def get(self, parent_asin: str) -> dict | None:
        return self.products.get(parent_asin)

    def contains(self, parent_asin: str) -> bool:
        return parent_asin in self.products


def build_category_lexicon(products: dict[str, dict]) -> tuple[str, ...]:
    """Unique catalog leaves and last-two crumbs, longest first."""
    entries: set[str] = set()
    for product in products.values():
        cats = product.get("categories") or []
        cleaned = [re.sub(r"\s+", " ", str(item).strip().lower()) for item in cats if item]
        cleaned = [item for item in cleaned if item]
        if not cleaned:
            continue
        entries.add(cleaned[-1])
        if len(cleaned) >= 2:
            entries.add(" ".join(cleaned[-2:]))
    return tuple(sorted(entries, key=lambda item: (-len(item), item)))
