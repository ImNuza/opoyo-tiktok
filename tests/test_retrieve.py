from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent.catalog import Catalog
from agent.retrieve import Retriever, build_query


def write_catalog(rows: list[dict]) -> Path:
    handle = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    for row in rows:
        handle.write(json.dumps(row) + "\n")
    handle.close()
    return Path(handle.name)


class RetrieveTest(unittest.TestCase):
    def setUp(self) -> None:
        path = write_catalog([
            {
                "parent_asin": "A",
                "title": "Blue running shoe",
                "categories": ["Shoes"],
                "features": ["mesh"],
                "details": {},
                "store": "Example",
                "description": "light running shoe",
            },
            {
                "parent_asin": "B",
                "title": "Black winter boot",
                "categories": ["Boots"],
                "features": ["leather"],
                "details": {},
                "store": "Example",
                "description": "warm boot",
            },
        ])
        self.catalog = Catalog(path)
        self.retriever = Retriever(self.catalog)

    def test_title_fragment_ranks_matching_product(self) -> None:
        ids = self.retriever.search("blue running shoe", limit=10)
        self.assertGreaterEqual(len(ids), 1)
        self.assertEqual(ids[0], "A")
        self.assertTrue(set(ids) <= self.catalog.ids)

    def test_empty_query_returns_empty(self) -> None:
        self.assertEqual(self.retriever.search("", limit=10), [])

    def test_build_query_includes_slots(self) -> None:
        q = build_query("need this", {"color": "red", "category": "jacket"})
        self.assertIn("red", q)
        self.assertIn("jacket", q)
        self.assertIn("need this", q)

    def test_required_terms_and_instead_of_or_blast(self) -> None:
        path = write_catalog([
            {
                "parent_asin": "HIT",
                "title": "Red running shoe",
                "categories": ["Shoes"],
                "features": ["mesh"],
                "details": {},
                "store": "Example",
                "description": "red running shoe",
            },
            {
                "parent_asin": "NOISE",
                "title": "Red winter coat",
                "categories": ["Jackets"],
                "features": ["wool"],
                "details": {},
                "store": "Example",
                "description": "red coat",
            },
        ])
        retriever = Retriever(Catalog(path))
        or_ids = retriever.search("red running shoe", limit=10)
        self.assertEqual(set(or_ids), {"HIT", "NOISE"})
        and_ids = retriever.search(
            "red running shoe",
            limit=10,
            required=["red", "shoe"],
        )
        self.assertEqual(and_ids, ["HIT"])


if __name__ == "__main__":
    unittest.main()
