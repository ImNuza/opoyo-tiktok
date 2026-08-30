from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent.catalog import Catalog
from agent.retrieve import Retriever, _terms, build_query, expand_terms


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

    def test_build_query_includes_profile_tags(self) -> None:
        q = build_query("blue shoe", {"color": "blue"}, extra=["fit", "comfort"])
        self.assertIn("fit", q)
        self.assertIn("comfort", q)
        self.assertIn("blue", q)

    def test_template_junk_is_not_a_query_term(self) -> None:
        terms = _terms("I'm looking for Dresses Casual. A key requirement is: fabric.")
        self.assertIn("dresses", terms)
        self.assertIn("casual", terms)
        self.assertIn("fabric", terms)
        self.assertNotIn("key", terms)
        self.assertNotIn("requirement", terms)
        self.assertNotIn("looking", terms)

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
        or_ids = retriever.search("red", limit=10)
        self.assertEqual(set(or_ids), {"HIT", "NOISE"})
        and_ids = retriever.search(
            "red running shoe",
            limit=10,
            required=["red", "shoe"],
        )
        self.assertEqual(and_ids, ["HIT"])

    def test_shoes_hypernym_retrieves_clog(self) -> None:
        path = write_catalog([
            {
                "parent_asin": "CLOG",
                "title": "Crocs Classic Clog",
                "categories": ["Mules & Clogs"],
                "features": ["croslite"],
                "details": {},
                "store": "Crocs",
                "description": "classic clog",
            },
            {
                "parent_asin": "COAT",
                "title": "Red winter coat",
                "categories": ["Jackets"],
                "features": ["wool"],
                "details": {},
                "store": "Example",
                "description": "red coat",
            },
        ])
        retriever = Retriever(Catalog(path))
        ids = retriever.search("shoes", limit=10, required=["shoes"])
        self.assertIn("CLOG", ids)
        self.assertNotIn("COAT", ids)

    def test_rain_expansion_retrieves_raincoat(self) -> None:
        path = write_catalog([
            {
                "parent_asin": "RAIN",
                "title": "Asgard waterproof raincoat",
                "categories": ["Outdoor"],
                "features": ["waterproof"],
                "details": {},
                "store": "Asgard",
                "description": "rain coat",
            },
            {
                "parent_asin": "HAT",
                "title": "Wool beanie",
                "categories": ["Hats"],
                "features": ["wool"],
                "details": {},
                "store": "Example",
                "description": "warm hat",
            },
        ])
        retriever = Retriever(Catalog(path))
        ids = retriever.search("Outdoor Work Rain", limit=10)
        self.assertIn("RAIN", ids)

    def test_clog_query_and_family_without_required(self) -> None:
        path = write_catalog([
            {
                "parent_asin": "CLOG",
                "title": "Crocs Classic Clog",
                "categories": ["Mules & Clogs"],
                "features": ["croslite"],
                "details": {},
                "store": "Crocs",
                "description": "classic clog",
            },
            {
                "parent_asin": "COAT",
                "title": "Comfort wool coat",
                "categories": ["Jackets"],
                "features": ["wool", "comfort"],
                "details": {},
                "store": "Example",
                "description": "warm coat",
            },
        ])
        retriever = Retriever(Catalog(path))
        ids = retriever.search("mules clogs comfort", limit=10)
        self.assertIn("CLOG", ids)
        self.assertNotIn("COAT", ids)

    def test_expand_terms_footwear(self) -> None:
        expanded = expand_terms(["shoes"])
        self.assertIn("clog", expanded)
        self.assertIn("mule", expanded)
        self.assertIn("sneaker", expanded)

    def test_expand_terms_from_clog(self) -> None:
        expanded = expand_terms(["clog"])
        self.assertIn("shoes", expanded)
        self.assertIn("mule", expanded)
        self.assertIn("boot", expanded)

    def test_expand_terms_from_billfold(self) -> None:
        expanded = expand_terms(["billfold"])
        self.assertIn("wallet", expanded)
        self.assertIn("wallets", expanded)


if __name__ == "__main__":
    unittest.main()
