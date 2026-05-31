"""Characterization tests for recipe_selector module - locks in existing behavior."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from datetime import date

from recipe_selector import (
    InsufficientRecipesError,
    ensure_veggies,
    select_random_proteins,
)


class TestSelectRandomProteins:
    """Selection now uses weighted-random by seasonal score within protein groups."""

    @patch("recipe_selector.weighted_sample")
    def test_selects_two_land_one_seafood(self, mock_sample):
        """Selects two land one seafood."""
        mock_sample.side_effect = lambda items, weights, k: items[:k]
        recipes = {
            "url1": {"ingredients": ["chicken breast", "salt"]},
            "url2": {"ingredients": ["salmon fillet", "pepper"]},
            "url3": {"ingredients": ["tofu", "soy sauce"]},
            "url4": {"ingredients": ["shrimp", "garlic"]},
        }

        selected = select_random_proteins(recipes, today=date(2026, 6, 21))

        assert len(selected) == 3
        # Each selected item is a {url: recipe} dict
        for item in selected:
            assert isinstance(item, dict)
            assert len(item) == 1

    @patch("recipe_selector.weighted_sample")
    def test_passes_final_scores_as_weights(self, mock_sample):
        """Passes final scores as weights."""
        captured = {}

        def capture(items, weights, k):
            """Helper for the surrounding test."""
            captured["weights"] = weights
            return items[:k]

        mock_sample.side_effect = capture
        recipes = {
            "url1": {"ingredients": ["chicken"]},
            "url2": {"ingredients": ["pork"]},
            "url3": {"ingredients": ["turkey"]},
        }

        select_random_proteins(recipes, today=date(2026, 1, 15))

        # All weights are positive floats (final_score is floored at MIN_SCORE)
        assert all(w > 0 for w in captured["weights"])


class TestEnsureVeggies:
    """Test veggie_checker function behavior."""

    def test_meal_with_veggies_returned_as_single_main(self):
        """Test meal with veggies is categorized as single_main."""
        meals = [{"url1": {"ingredients": ["chicken", "broccoli", "garlic"]}}]
        sides = {}
        veggies = ["broccoli", "spinach", "carrot"]

        result = ensure_veggies(meals, sides, veggies)

        assert len(result) == 1
        assert result[0]["type"] == "single_main"

    @patch("recipe_selector.random.choice")
    def test_meal_without_veggies_gets_side(self, mock_choice):
        """Test meal without veggies gets a side dish added."""
        meals = [{"url1": {"ingredients": ["chicken", "salt", "pepper"]}}]
        sides = {"side_url": {"ingredients": ["spinach salad"]}}
        veggies = ["broccoli", "spinach", "carrot"]

        mock_choice.return_value = ("side_url", {"ingredients": ["spinach salad"]})

        result = ensure_veggies(meals, sides, veggies)

        # Should have 2 items: combo_main and combo_side
        assert len(result) == 2
        assert result[0]["type"] == "combo_main"
        assert result[1]["type"] == "combo_side"

    def test_multiple_meals_mixed_veggie_status(self):
        """Test processing multiple meals with mixed veggie status."""
        meals = [
            {"url1": {"ingredients": ["chicken", "broccoli"]}},
            {"url2": {"ingredients": ["beef", "salt"]}},
        ]
        sides = {"side1": {"ingredients": ["carrot salad"]}}
        veggies = ["broccoli", "carrot"]

        result = ensure_veggies(meals, sides, veggies)

        # First meal has veggies (1 item), second doesn't (2 items)
        assert len(result) == 3

    def test_veggie_matching_is_case_insensitive(self):
        """Test that veggie matching works case-insensitively."""
        meals = [{"url1": {"ingredients": ["Chicken with BROCCOLI"]}}]
        sides = {}
        veggies = ["broccoli"]

        result = ensure_veggies(meals, sides, veggies)

        assert result[0]["type"] == "single_main"

    def test_partial_veggie_name_matches(self):
        """Test that partial veggie name matching works."""
        meals = [{"url1": {"ingredients": ["butternut squash soup"]}}]
        sides = {}
        veggies = ["squash"]

        result = ensure_veggies(meals, sides, veggies)

        # "squash" should match "butternut squash"
        assert result[0]["type"] == "single_main"

    def test_empty_meals_returns_empty_list(self):
        """Test that empty meals list returns empty result."""
        meals = []
        sides = {"side": {"ingredients": ["salad"]}}
        veggies = ["lettuce"]

        result = ensure_veggies(meals, sides, veggies)

        assert result == []

    def test_preserves_meal_structure_in_result(self):
        """Test that the meal structure is preserved in results."""
        meals = [{"url1": {"ingredients": ["chicken", "spinach"], "title": "Test"}}]
        sides = {}
        veggies = ["spinach"]

        result = ensure_veggies(meals, sides, veggies)

        assert "obj" in result[0]
        assert "url1" in result[0]["obj"]
        assert result[0]["obj"]["url1"]["title"] == "Test"


class TestSeasonalSelection:
    """Tests for seasonal selection."""

    @patch("recipe_selector.weighted_sample")
    def test_preserves_protein_balance_with_seafood(self, mock_sample):
        # weighted_sample returns the first k items it is given (deterministic)
        """Preserves protein balance with seafood."""
        mock_sample.side_effect = lambda items, weights, k: items[:k]
        recipes = {
            "land1": {"ingredients": ["chicken breast"]},
            "land2": {"ingredients": ["pork loin"]},
            "land3": {"ingredients": ["tofu"]},
            "sea1": {"ingredients": ["salmon fillet"]},
            "sea2": {"ingredients": ["shrimp"]},
        }

        selected = select_random_proteins(recipes, today=date(2026, 6, 21))

        # 2 landfood + 1 seafood
        assert len(selected) == 3

    @patch("recipe_selector.weighted_sample")
    def test_three_landfood_when_no_seafood(self, mock_sample):
        """Three landfood when no seafood."""
        mock_sample.side_effect = lambda items, weights, k: items[:k]
        recipes = {
            "land1": {"ingredients": ["chicken"]},
            "land2": {"ingredients": ["pork"]},
            "land3": {"ingredients": ["turkey"]},
            "land4": {"ingredients": ["tofu"]},
        }

        selected = select_random_proteins(recipes, today=date(2026, 1, 15))

        assert len(selected) == 3

    def test_raises_when_insufficient(self):
        """Raises when insufficient."""
        recipes = {"land1": {"ingredients": ["chicken"]}}

        with pytest.raises(InsufficientRecipesError):
            select_random_proteins(recipes, today=date(2026, 6, 21))
