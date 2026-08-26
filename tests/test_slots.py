from __future__ import annotations

import unittest

from agent.slots import parse_slots


class SlotsTest(unittest.TestCase):
    def test_parses_color_and_material(self) -> None:
        slots = parse_slots("I want a red leather jacket")
        self.assertEqual(slots.get("color"), "red")
        self.assertEqual(slots.get("material"), "leather")
        self.assertEqual(slots.get("category"), "jacket")

    def test_parses_budget(self) -> None:
        slots = parse_slots("looking for boots under $50")
        self.assertEqual(slots.get("budget"), "50")
        self.assertEqual(slots.get("category"), "boots")

    def test_uses_profile_tags_as_brand_prior(self) -> None:
        slots = parse_slots("need shoes", {"preference_tags": ["Nike", "red"]})
        self.assertEqual(slots.get("brand"), "Nike")
        self.assertEqual(slots.get("category"), "shoes")

    def test_empty_message(self) -> None:
        self.assertEqual(parse_slots(""), {})


if __name__ == "__main__":
    unittest.main()
