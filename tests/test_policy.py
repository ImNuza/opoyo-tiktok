from __future__ import annotations

import unittest

from agent.policy import ASK, FIELD_ORDER, RETRIEVE, decide
from agent.state import new_state


class PolicyTest(unittest.TestCase):
    def test_turn_10_always_retrieves(self) -> None:
        state = new_state("s", {})
        action, attr = decide(state, turn=10)
        self.assertEqual(action, RETRIEVE)
        self.assertIsNone(attr)

    def test_buying_hard_constraint_retrieves(self) -> None:
        state = new_state("s", {})
        state.slots["color"] = "red"
        action, attr = decide(state, turn=1)
        self.assertEqual(action, RETRIEVE)
        self.assertIsNone(attr)

    def test_browsing_vague_asks_category(self) -> None:
        state = new_state("s", {})
        action, attr = decide(state, turn=1)
        self.assertEqual(action, ASK)
        self.assertEqual(attr, "category")

    def test_does_not_reask(self) -> None:
        state = new_state("s", {})
        state.asked.add("category")
        action, attr = decide(state, turn=2)
        self.assertEqual(action, ASK)
        self.assertEqual(attr, "budget")

    def test_huge_pool_asks_missing_field(self) -> None:
        state = new_state("s", {})
        state.slots["color"] = "red"
        action, attr = decide(state, turn=2, candidate_count=200)
        self.assertEqual(action, ASK)
        self.assertEqual(attr, "category")

    def test_style_only_asks_category(self) -> None:
        state = new_state("s", {})
        state.slots["style"] = "casual"
        action, attr = decide(state, turn=1)
        self.assertEqual(action, ASK)
        self.assertEqual(attr, "category")

    def test_exhausted_field_order_retrieves(self) -> None:
        state = new_state("s", {})
        for field in FIELD_ORDER:
            state.asked.add(field)
        action, attr = decide(state, turn=1)
        self.assertEqual(action, RETRIEVE)
        self.assertIsNone(attr)

    def test_candidate_count_80_with_hard_constraint_retrieves(self) -> None:
        state = new_state("s", {})
        state.slots["color"] = "red"
        action, attr = decide(state, turn=1, candidate_count=80)
        self.assertEqual(action, RETRIEVE)
        self.assertIsNone(attr)


if __name__ == "__main__":
    unittest.main()
