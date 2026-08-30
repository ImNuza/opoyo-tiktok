from __future__ import annotations

import unittest

from agent.router import (
    BOUNDARY,
    BROWSING,
    BUYING,
    OTHER,
    OVERRIDE,
    classify_track,
    looking_for_crumb,
)


class RouterTest(unittest.TestCase):
    def test_buying_template(self) -> None:
        message = "I'm looking for Dresses Casual. A key requirement is: fabric."
        self.assertEqual(classify_track(message), BUYING)
        self.assertEqual(looking_for_crumb(message), "Dresses Casual")

    def test_browsing_template(self) -> None:
        message = "I'm looking for Outdoor & Work Rain, but I'm still exploring."
        self.assertEqual(classify_track(message), BROWSING)
        self.assertEqual(looking_for_crumb(message), "Outdoor & Work Rain")

    def test_override_template(self) -> None:
        message = "Actually, ignore my earlier preference. What I need is: leather."
        self.assertEqual(classify_track(message), OVERRIDE)

    def test_override_starts_with_actually(self) -> None:
        self.assertEqual(classify_track("actually I want black boots"), OVERRIDE)

    def test_boundary_template(self) -> None:
        self.assertEqual(
            classify_track("I don't have a preference for color; please use your judgment."),
            BOUNDARY,
        )
        self.assertEqual(
            classify_track("I don't have an additional preference for style."),
            BOUNDARY,
        )

    def test_other_plain_request(self) -> None:
        self.assertEqual(classify_track("I want a blue running shoe"), OTHER)
        self.assertIsNone(looking_for_crumb("I want a blue running shoe"))


if __name__ == "__main__":
    unittest.main()
