from __future__ import annotations

import unittest

from agent.rerank import apply_order, clean_query_text, rerank


class RerankTest(unittest.TestCase):
    def test_no_key_returns_local_order(self) -> None:
        ids = ["A", "B", "C"]
        self.assertEqual(rerank(ids, "hello", {"color": "red"}, api_key=None), ids)

    def test_empty_key_returns_shortlist_unchanged(self) -> None:
        ids = ["A", "B", "C"]
        self.assertEqual(rerank(ids, "hello", {}, api_key=""), ids)

    def test_apply_order_drops_unknown_asins(self) -> None:
        shortlist = ["A", "B", "C"]
        proposed = ["Z", "C", "A", "Y"]
        self.assertEqual(apply_order(shortlist, proposed), ["C", "A"])

    def test_missing_texts_does_not_require_minilm(self) -> None:
        ids = ["A", "B"]
        self.assertEqual(rerank(ids, "blue shoe", {}, texts=None), ids)

    def test_clean_query_strips_simulator_wrappers(self) -> None:
        text = clean_query_text(
            "I'm looking for Dresses Casual, but I'm still exploring.",
            {"category": "dresses"},
        )
        self.assertIn("dresses", text.lower())
        self.assertNotIn("looking for", text.lower())
        self.assertNotIn("still exploring", text.lower())

    def test_clean_query_keeps_constraint_after_buying_wrapper(self) -> None:
        text = clean_query_text(
            "I'm looking for Running Shoes. A key requirement is: leather.",
            {"category": "shoes", "material": "leather"},
        )
        lowered = text.lower()
        self.assertIn("leather", lowered)
        self.assertNotIn("key requirement", lowered)


if __name__ == "__main__":
    unittest.main()
