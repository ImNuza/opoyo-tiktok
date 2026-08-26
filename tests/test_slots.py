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
        self.assertNotIn("brand", slots)
        self.assertEqual(slots.get("category"), "shoes")

    def test_preference_tags_fit_comfort_are_not_brand(self) -> None:
        slots = parse_slots("need shoes", {"preference_tags": ["fit", "comfort"]})
        self.assertNotIn("brand", slots)
        self.assertEqual(slots.get("category"), "shoes")

    def test_im_exploring_does_not_set_size(self) -> None:
        slots = parse_slots(
            "I'm looking for Running Shoes, but I'm still exploring."
        )
        self.assertNotIn("size", slots)

    def test_parses_size_m_and_size_10(self) -> None:
        self.assertEqual(parse_slots("need size m shoes").get("size"), "m")
        self.assertEqual(parse_slots("need size 10 shoes").get("size"), "10")

    def test_empty_message(self) -> None:
        self.assertEqual(parse_slots(""), {})


if __name__ == "__main__":
    unittest.main()
