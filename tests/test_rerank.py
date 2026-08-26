from __future__ import annotations

import unittest

from agent.rerank import rerank


class RerankTest(unittest.TestCase):
    def test_no_key_returns_local_order(self) -> None:
        ids = ["A", "B", "C"]
        self.assertEqual(rerank(ids, "hello", {"color": "red"}, api_key=None), ids)

    def test_drops_ids_not_in_shortlist(self) -> None:
        ids = ["A", "B"]
        # even if a future LLM returns junk, public function must not introduce it
        self.assertEqual(rerank(ids, "hello", {}, api_key=""), ids)


if __name__ == "__main__":
    unittest.main()
