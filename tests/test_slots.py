from __future__ import annotations

import unittest

from agent.slots import parse_slots, preference_snippet


class SlotsTest(unittest.TestCase):
    def test_parses_color_and_material(self) -> None:
        slots = parse_slots("I want a red leather jacket")
        self.assertEqual(slots.get("color"), "red")
        self.assertEqual(slots.get("material"), "leather")
        self.assertEqual(slots.get("category"), "jacket")

    def test_parses_plural_amazon_category_crumbs(self) -> None:
        dresses = parse_slots("I'm looking for Dresses Casual. A key requirement is: fabric.")
        self.assertEqual(dresses.get("category"), "dresses")
        jackets = parse_slots("I'm looking for Lightweight Jackets Windbreakers.")
        self.assertEqual(jackets.get("category"), "jackets")
        wallets = parse_slots("I'm looking for Card Cases & Money Organizers Wallets.")
        self.assertEqual(wallets.get("category"), "wallets")
        pants = parse_slots("I'm looking for Men Pants, but I'm still exploring.")
        self.assertEqual(pants.get("category"), "pants")
        robes = parse_slots("I'm looking for Sleep & Lounge Robes.")
        self.assertEqual(robes.get("category"), "robes")

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

    def test_crumb_fills_category_when_no_noun(self) -> None:
        slots = parse_slots(
            "I'm looking for Athletic Walking, but I'm still exploring."
        )
        self.assertEqual(slots.get("category"), "athletic walking")
        rain = parse_slots(
            "I'm looking for Outdoor & Work Rain, but I'm still exploring."
        )
        self.assertEqual(rain.get("category"), "outdoor & work rain")

    def test_named_noun_wins_over_crumb(self) -> None:
        slots = parse_slots(
            "I'm looking for Dresses Casual. A key requirement is: fabric."
        )
        self.assertEqual(slots.get("category"), "dresses")

    def test_leaf_noun_not_parent_crumb(self) -> None:
        tees = parse_slots(
            "I'm looking for Tees & Blouses T-Shirts. A key requirement is: cotton."
        )
        self.assertEqual(tees.get("category"), "shirts")
        tunics = parse_slots(
            "I'm looking for Tees & Blouses Tunics. A key requirement is: polyester."
        )
        self.assertEqual(tunics.get("category"), "tunics")
        tanks = parse_slots(
            "I'm looking for Shirts Tanks Tops. A key requirement is: polyester."
        )
        self.assertEqual(tanks.get("category"), "tanks")
        caps = parse_slots(
            "I'm looking for Hats & Caps Baseball Caps. A key requirement is: polyester."
        )
        self.assertEqual(caps.get("category"), "caps")

    def test_empty_message(self) -> None:
        self.assertEqual(parse_slots(""), {})

    def test_preference_snippet_from_evaluator_reply(self) -> None:
        self.assertEqual(
            preference_snippet("For that, what matters is: slim fit; breathable mesh."),
            "slim fit breathable mesh",
        )
        self.assertIsNone(
            preference_snippet("I don't have an additional preference for style.")
        )


if __name__ == "__main__":
    unittest.main()
