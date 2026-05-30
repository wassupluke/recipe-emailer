"""Characterization tests for seasonal_tagging module."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from seasonal_tagging import ensure_recipe_tagged, score_oven_use, score_seasons


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


def _ollama_response(payload_str: str) -> Mock:
    """Build a mock requests Response whose .json() returns {'response': payload_str}."""
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = {"response": payload_str}
    return resp


class TestScoreSeasons:
    @patch("seasonal_tagging.requests.post")
    def test_valid_json_returns_scores(self, mock_post: Mock):
        mock_post.return_value = _ollama_response(
            json.dumps({"spring": 0.2, "summer": 0.9, "fall": 0.4, "winter": 0.1})
        )

        result = score_seasons("Grilled Summer Salad", ["tomato", "basil"])

        assert result == {"spring": 0.2, "summer": 0.9, "fall": 0.4, "winter": 0.1}
        assert mock_post.call_count == 1

    @patch("seasonal_tagging.requests.post")
    def test_malformed_then_valid_retries_once(self, mock_post: Mock):
        mock_post.side_effect = [
            _ollama_response("not json at all"),
            _ollama_response(
                json.dumps({"spring": 0.1, "summer": 0.1, "fall": 0.1, "winter": 0.9})
            ),
        ]

        result = score_seasons("Winter Stew", ["beef", "potato"])

        assert result == {"spring": 0.1, "summer": 0.1, "fall": 0.1, "winter": 0.9}
        assert mock_post.call_count == 2

    @patch("seasonal_tagging.requests.post")
    def test_persistent_malformed_returns_none(self, mock_post: Mock):
        mock_post.return_value = _ollama_response("still not json")

        result = score_seasons("Mystery Dish", ["stuff"])

        assert result is None
        assert mock_post.call_count == 2  # original + one retry

    @patch("seasonal_tagging.requests.post")
    def test_missing_key_is_invalid_returns_none(self, mock_post: Mock):
        mock_post.return_value = _ollama_response(
            json.dumps({"spring": 0.2, "summer": 0.9, "fall": 0.4})  # no winter
        )

        result = score_seasons("Partial", ["x"])

        assert result is None
        assert mock_post.call_count == 2

    @patch("seasonal_tagging.requests.post")
    def test_connection_error_returns_none_after_retry(self, mock_post: Mock):
        mock_post.side_effect = requests.exceptions.ConnectionError()

        result = score_seasons("Offline", ["x"])

        assert result is None
        assert mock_post.call_count == 2

    @patch("seasonal_tagging.requests.post")
    def test_out_of_range_values_are_clamped(self, mock_post: Mock):
        mock_post.return_value = _ollama_response(
            json.dumps({"spring": -0.2, "summer": 1.4, "fall": 0.4, "winter": 0.1})
        )

        result = score_seasons("Clamp", ["x"])

        assert result == {"spring": 0.0, "summer": 1.0, "fall": 0.4, "winter": 0.1}

    @patch("seasonal_tagging.requests.post")
    def test_non_dict_json_body_returns_none(self, mock_post: Mock):
        resp = Mock()
        resp.status_code = 200
        resp.json.return_value = [1, 2, 3]  # JSON array, not an object
        mock_post.return_value = resp

        result = score_seasons("Weird", ["x"])

        assert result is None


class TestEnsureRecipeTagged:
    @patch("seasonal_tagging.score_seasons")
    def test_adds_both_keys_when_seasons_available(self, mock_seasons: Mock):
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

    @patch("seasonal_tagging.score_seasons")
    def test_leaves_seasonality_absent_when_model_fails(self, mock_seasons: Mock):
        mock_seasons.return_value = None
        recipe = {
            "title": "Baked Ziti",
            "ingredients": ["pasta"],
            "instructions": "Bake at 375",
        }

        changed = ensure_recipe_tagged(recipe)

        # oven_use was still added by rules, so something changed
        assert changed is True
        assert recipe["oven_use"] == 1.0
        assert "seasonality" not in recipe

    @patch("seasonal_tagging.score_seasons")
    def test_fully_tagged_recipe_is_unchanged(self, mock_seasons: Mock):
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
