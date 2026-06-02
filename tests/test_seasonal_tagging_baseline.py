"""Characterization tests for seasonal_tagging module.

oven_use is rule-based; seasonality is delegated to the local numpy student
model (patched here), so no network is involved.
"""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))
import seasonal_tagging
from seasonal_tagging import ensure_recipe_tagged, score_oven_use


class TestScoreOvenUse:
    """Tests for score oven use."""

    def test_oven_keywords_score_one(self):
        """Oven keywords score one."""
        assert score_oven_use("Bake at 425 for 20 minutes") == 1.0
        assert score_oven_use("Roast the vegetables in the oven") == 1.0
        assert score_oven_use("Broil until golden") == 1.0

    def test_grill_and_no_cook_score_zero(self):
        """Grill and no cook score zero."""
        assert score_oven_use("Grill the chicken over medium heat") == 0.0
        assert score_oven_use("No-cook overnight oats, refrigerate until set") == 0.0
        assert score_oven_use("Blend everything and serve chilled") == 0.0

    def test_stovetop_scores_half(self):
        """Stovetop scores half."""
        assert score_oven_use("Simmer in a skillet for 10 minutes") == 0.5
        assert score_oven_use("Saute the onions until soft") == 0.5

    def test_oven_wins_over_other_keywords(self):
        # Contains both 'grill' and 'bake' -> oven wins
        """Oven wins over other keywords."""
        assert score_oven_use("Grill marks optional; bake at 400 to finish") == 1.0

    def test_no_keywords_defaults_to_half(self):
        """No keywords defaults to half."""
        assert score_oven_use("Combine all ingredients in a bowl") == 0.5


class TestScoreSeasonsStudent:
    """Tests for score_seasons backed by the numpy student."""

    @patch("seasonal_tagging.predict_for_recipe")
    def test_delegates_to_student_no_network(self, mock_predict: Any) -> None:
        """score_seasons returns the student's 4-float dict, no network call."""
        mock_predict.return_value = {
            "spring": 0.1,
            "summer": 0.9,
            "fall": 0.0,
            "winter": 0.0,
        }
        out = seasonal_tagging.score_seasons(
            {"title": "Gazpacho", "ingredients": ["tomato"]}
        )
        assert out == {"spring": 0.1, "summer": 0.9, "fall": 0.0, "winter": 0.0}
        mock_predict.assert_called_once()


class TestEnsureRecipeTagged:
    """Tests for ensure recipe tagged."""

    @patch("seasonal_tagging.score_seasons")
    def test_adds_both_keys_from_student(self, mock_seasons: Mock) -> None:
        """oven_use (rules) and seasonality (student) are both added."""
        mock_seasons.return_value = {
            "spring": 0.2,
            "summer": 0.9,
            "fall": 0.4,
            "winter": 0.1,
        }
        recipe = {
            "title": "Grilled Veg",
            "ingredients": ["zucchini"],
            "instructions": "Grill until charred",
        }

        changed = ensure_recipe_tagged(recipe)

        assert changed is True
        assert recipe["oven_use"] == 0.0
        assert recipe["seasonality"]["summer"] == 0.9
        mock_seasons.assert_called_once_with(recipe)

    @patch("seasonal_tagging.score_seasons")
    def test_fully_tagged_recipe_is_unchanged(self, mock_seasons: Mock) -> None:
        """Fully tagged recipe is unchanged."""
        recipe = {
            "title": "X",
            "ingredients": ["y"],
            "instructions": "Bake",
            "oven_use": 1.0,
            "seasonality": {"spring": 0.1, "summer": 0.1, "fall": 0.1, "winter": 0.1},
        }

        changed = ensure_recipe_tagged(recipe)

        assert changed is False
        mock_seasons.assert_not_called()
