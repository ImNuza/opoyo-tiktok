from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from starter.agent import Agent


ALLOWED = {
    "category", "material", "color", "size", "style", "brand",
    "budget", "feature", "use_case", "other", None,
}


def write_catalog(rows: list[dict]) -> Path:
    handle = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    for row in rows:
        handle.write(json.dumps(row) + "\n")
    handle.close()
    return Path(handle.name)


class AgentWrapperTest(unittest.TestCase):
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
        self.agent = Agent(path)

    def test_missing_catalog_raises(self) -> None:
        from agent.catalog import CatalogError
        with self.assertRaises(CatalogError):
            Agent("/tmp/missing-opoyo-catalog.jsonl")

    def test_contract_keys_and_ask_attribute(self) -> None:
        self.agent.reset("s1", {"preference_tags": [], "summary": "x"})
        out = self.agent.respond("s1", "hi", turn=1, top_k=10)
        self.assertIn("message", out)
        self.assertIn("ask_attribute", out)
        self.assertIn("recommendations", out)
        self.assertIn(out["ask_attribute"], ALLOWED)
        for row in out["recommendations"]:
            self.assertIn("parent_asin", row)
            self.assertIn(row["parent_asin"], {"A", "B"})

    def test_buying_returns_ids_and_does_not_ask(self) -> None:
        self.agent.reset("s1", {})
        out = self.agent.respond("s1", "I want a blue running shoe", turn=1, top_k=10)
        self.assertIsNone(out["ask_attribute"])
        self.assertGreaterEqual(len(out["recommendations"]), 1)
        self.assertEqual(out["recommendations"][0]["parent_asin"], "A")

    def test_turn_10_never_asks(self) -> None:
        self.agent.reset("s1", {})
        out = self.agent.respond("s1", "hi", turn=10, top_k=10)
        self.assertIsNone(out["ask_attribute"])

    def test_turn_10_empty_slots_returns_catalog_asins(self) -> None:
        self.agent.reset("s1", {})
        out = self.agent.respond("s1", "hi", turn=10, top_k=10)
        self.assertIsNone(out["ask_attribute"])
        recs = out["recommendations"]
        self.assertEqual(len(recs), 2)
        asins = [row["parent_asin"] for row in recs]
        self.assertEqual(asins, list(dict.fromkeys(asins)))
        self.assertTrue(set(asins) <= {"A", "B"})
        self.assertEqual(set(asins), {"A", "B"})

    def test_override_switches_color_slot(self) -> None:
        self.agent.reset("s1", {})
        self.agent.respond("s1", "red leather jacket", turn=1, top_k=10)
        out = self.agent.respond("s1", "actually I want black boots", turn=4, top_k=10)
        self.assertEqual(self.agent._sessions["s1"].slots.get("color"), "black")
        asins = [row["parent_asin"] for row in out["recommendations"]]
        self.assertTrue(set(asins) <= {"A", "B"})

    def test_respond_without_reset_does_not_raise(self) -> None:
        out = self.agent.respond("ghost", "blue shoe", turn=1, top_k=10)
        self.assertIn("recommendations", out)

    def test_huge_pool_hard_constraint_asks(self) -> None:
        rows = [
            {
                "parent_asin": f"P{i}",
                "title": f"Red running shoe {i}",
                "categories": ["Shoes"],
                "features": ["mesh"],
                "details": {},
                "store": "Example",
                "description": "red running shoe",
            }
            for i in range(90)
        ]
        agent = Agent(write_catalog(rows))
        agent.reset("s1", {})
        out = agent.respond("s1", "I want red", turn=1, top_k=10)
        self.assertEqual(out["ask_attribute"], "category")
        self.assertGreaterEqual(len(out["recommendations"]), 1)


if __name__ == "__main__":
    unittest.main()
