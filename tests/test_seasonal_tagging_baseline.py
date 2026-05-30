"""Characterization tests for seasonal_tagging module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from seasonal_tagging import score_oven_use


class TestScoreOvenUse:
    def test_oven_keywords_score_one(self):
        assert score_oven_use("Bake at 425 for 20 minutes") == 1.0
        assert score_oven_use("Roast the vegetables in the oven") == 1.0
        assert score_oven_use("Broil until golden") == 1.0

    def test_grill_and_no_cook_score_zero(self):
        assert score_oven_use("Grill the chicken over medium heat") == 0.0
        assert score_oven_use("No-cook overnight oats, refrigerate until set") == 0.0
        assert score_oven_use("Blend everything and serve chilled") == 0.0

    def test_stovetop_scores_half(self):
        assert score_oven_use("Simmer in a skillet for 10 minutes") == 0.5
        assert score_oven_use("Saute the onions until soft") == 0.5

    def test_oven_wins_over_other_keywords(self):
        # Contains both 'grill' and 'bake' -> oven wins
        assert score_oven_use("Grill marks optional; bake at 400 to finish") == 1.0

    def test_no_keywords_defaults_to_half(self):
        assert score_oven_use("Combine all ingredients in a bowl") == 0.5
