from __future__ import annotations

import unittest

from agent.state import apply_override, clear_intent, new_state


class StateTest(unittest.TestCase):
    def test_new_state_is_empty(self) -> None:
        state = new_state("s1", {"summary": "x"})
        self.assertEqual(state.slots, {})
        self.assertEqual(state.asked, set())
        self.assertEqual(state.profile["summary"], "x")

    def test_override_erases_old_slot_and_allows_reask(self) -> None:
        state = new_state("s1", {})
        state.slots["color"] = "red"
        state.asked.add("color")
        apply_override(state, "color", "blue")
        self.assertEqual(state.slots["color"], "blue")
        self.assertNotIn("color", state.asked)

    def test_clear_intent_wipes_slots_and_asked(self) -> None:
        state = new_state("s1", {})
        state.slots["color"] = "red"
        state.slots["style"] = "running"
        state.asked.add("color")
        state.last_asked = "color"
        clear_intent(state)
        self.assertEqual(state.slots, {})
        self.assertEqual(state.asked, set())
        self.assertIsNone(state.last_asked)


if __name__ == "__main__":
    unittest.main()
