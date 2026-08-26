from __future__ import annotations

import unittest

from agent.rerank import apply_order, rerank


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


if __name__ == "__main__":
    unittest.main()
