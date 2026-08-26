from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent.catalog import Catalog, CatalogError


class CatalogTest(unittest.TestCase):
    def _write(self, rows: list[dict]) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
        for row in rows:
            handle.write(json.dumps(row) + "\n")
        handle.close()
        return Path(handle.name)

    def test_indexes_by_parent_asin(self) -> None:
        path = self._write([
            {"parent_asin": "A", "title": "Blue shoe"},
            {"parent_asin": "B", "title": "Red hat"},
        ])
        catalog = Catalog(path)
        self.assertEqual(catalog.ids, {"A", "B"})
        self.assertEqual(catalog.get("A")["title"], "Blue shoe")
        self.assertTrue(catalog.contains("A"))
        self.assertFalse(catalog.contains("Z"))

    def test_missing_file_raises(self) -> None:
        with self.assertRaises(CatalogError) as ctx:
            Catalog("/tmp/does-not-exist-opoyo-catalog.jsonl")
        self.assertIn("does-not-exist-opoyo-catalog.jsonl", str(ctx.exception))

    def test_empty_file_raises(self) -> None:
        path = self._write([])
        with self.assertRaises(CatalogError):
            Catalog(path)


if __name__ == "__main__":
    unittest.main()
