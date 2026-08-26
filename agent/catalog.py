from __future__ import annotations

import json
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

    def get(self, parent_asin: str) -> dict | None:
        return self.products.get(parent_asin)

    def contains(self, parent_asin: str) -> bool:
        return parent_asin in self.products
