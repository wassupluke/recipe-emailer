"""Characterization tests for recipe_selector module - locks in existing behavior."""

from pathlib import Path
from unittest.mock import patch
import pytest
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from recipe_selector import select_random_proteins, ensure_veggies


class TestSelectRandomProteins:
    """Test get_random_proteins function behavior."""

    @patch('recipe_selector.random.sample')
    @patch('recipe_selector.random.shuffle')
    def test_selects_seafood_and_landfood_when_both_available(self, mock_shuffle, mock_sample):
        """Test selection when both seafood and landfood are available."""
        recipes = {
            "url1": {"ingredients": ["chicken breast", "salt"]},
            "url2": {"ingredients": ["salmon fillet", "pepper"]},
            "url3": {"ingredients": ["tofu", "soy sauce"]},
            "url4": {"ingredients": ["shrimp", "garlic"]},
        }
        
        # Mock sample to return specific meals
        def sample_side_effect(lst, k):
            return lst[:k]
        
        mock_sample.side_effect = sample_side_effect
        
        result = select_random_proteins(recipes)
        
        # Should have 3 total meals (2 landfood + 1 seafood)
        assert len(result) == 3

    def test_categorizes_seafood_correctly(self):
        """Test that seafood proteins are identified."""
        recipes = {
            "url1": {"ingredients": ["salmon", "lemon"]},
            "url2": {"ingredients": ["chicken", "salt"]},
            "url3": {"ingredients": ["turkey", "herbs"]},
        }
        
        result = select_random_proteins(recipes)
        
        # Should find the salmon recipe
        assert any("salmon" in str(meal).lower() for meal in result)

    def test_categorizes_landfood_correctly(self):
        """Test that land-based proteins are identified."""
        recipes = {
            "url1": {"ingredients": ["chicken breast", "herbs"]},
            "url2": {"ingredients": ["turkey tenderloin", "spices"]},
            "url3": {"ingredients": ["pork chops", "garlic"]},
        }
        
        result = select_random_proteins(recipes)
        
        # All should be landfood
        assert len(result) >= 1

    @patch('recipe_selector.random.sample')
    @patch('recipe_selector.random.shuffle')  
    def test_returns_three_landfood_when_no_seafood(self, mock_shuffle, mock_sample):
        """Test returns 3 landfood meals when no seafood available."""
        recipes = {
            "url1": {"ingredients": ["chicken", "salt"]},
            "url2": {"ingredients": ["turkey", "pepper"]},
            "url3": {"ingredients": ["tofu", "soy"]},
            "url4": {"ingredients": ["chickpea", "cumin"]},
        }
        
        def sample_side_effect(lst, k):
            return lst[:k]
        
        mock_sample.side_effect = sample_side_effect
        
        result = select_random_proteins(recipes)
        
        assert len(result) == 3

    def test_exits_when_insufficient_meals(self):
        """Test that exception is raised when insufficient meals."""
        from recipe_selector import InsufficientRecipesError
        
        recipes = {
            "url1": {"ingredients": ["chicken", "salt"]},
        }
        
        # Should raise InsufficientRecipesError when not enough meals
        with pytest.raises(InsufficientRecipesError):
            select_random_proteins(recipes)

    def test_handles_recipe_with_invalid_ingredients(self):
        """Test handling of recipes with None or invalid ingredients."""
        from recipe_selector import InsufficientRecipesError
        
        recipes = {
            "url1": {"ingredients": ["chicken", "salt"]},
            "url2": {"ingredients": None},  # Invalid
            "url3": {"ingredients": ["salmon", "dill"]},
        }
        
        # Should raise InsufficientRecipesError (not enough valid recipes)
        with pytest.raises(InsufficientRecipesError):
            select_random_proteins(recipes)


class TestEnsureVeggies:
    """Test veggie_checker function behavior."""

    def test_meal_with_veggies_returned_as_single_main(self):
        """Test meal with veggies is categorized as single_main."""
        meals = [
            {"url1": {"ingredients": ["chicken", "broccoli", "garlic"]}}
        ]
        sides = {}
        veggies = ["broccoli", "spinach", "carrot"]
        
        result = ensure_veggies(meals, sides, veggies)
        
        assert len(result) == 1
        assert result[0]["type"] == "single_main"

    @patch('recipe_selector.random.choice')
    def test_meal_without_veggies_gets_side(self, mock_choice):
        """Test meal without veggies gets a side dish added."""
        meals = [
            {"url1": {"ingredients": ["chicken", "salt", "pepper"]}}
        ]
        sides = {
            "side_url": {"ingredients": ["spinach salad"]}
        }
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
        sides = {
            "side1": {"ingredients": ["carrot salad"]}
        }
        veggies = ["broccoli", "carrot"]
        
        result = ensure_veggies(meals, sides, veggies)
        
        # First meal has veggies (1 item), second doesn't (2 items)
        assert len(result) == 3

    def test_veggie_matching_is_case_insensitive(self):
        """Test that veggie matching works case-insensitively."""
        meals = [
            {"url1": {"ingredients": ["Chicken with BROCCOLI"]}}
        ]
        sides = {}
        veggies = ["broccoli"]
        
        result = ensure_veggies(meals, sides, veggies)
        
        assert result[0]["type"] == "single_main"

    def test_partial_veggie_name_matches(self):
        """Test that partial veggie name matching works."""
        meals = [
            {"url1": {"ingredients": ["butternut squash soup"]}}
        ]
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
        meals = [
            {"url1": {"ingredients": ["chicken", "spinach"], "title": "Test"}}
        ]
        sides = {}
        veggies = ["spinach"]
        
        result = ensure_veggies(meals, sides, veggies)
        
        assert "obj" in result[0]
        assert "url1" in result[0]["obj"]
        assert result[0]["obj"]["url1"]["title"] == "Test"
