"""Tests for the pure-numpy distilled seasonality student model."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import seasonal_model


class TestTokenize:
    """Tests for tokenize."""

    def test_lowercases_and_splits_on_word_boundaries(self) -> None:
        """Tokenizer lowercases and keeps word tokens of length >= 2."""
        assert seasonal_model.tokenize("Fresh BASIL, tomatoes!") == [
            "fresh",
            "basil",
            "tomatoes",
        ]

    def test_drops_single_char_tokens(self) -> None:
        """Single-character tokens are dropped (matches sklearn default)."""
        assert seasonal_model.tokenize("a big o") == ["big"]


class TestRecipeText:
    """Tests for recipe_text."""

    def test_concatenates_title_ingredients_keywords(self) -> None:
        """Text blob joins title, ingredients, and keywords."""
        recipe = {
            "title": "Squash Soup",
            "ingredients": ["1 butternut squash", "2 cups broth"],
            "keywords": ["fall", "cozy"],
        }
        blob = seasonal_model.recipe_text(recipe)
        assert "squash soup" in blob.lower()
        assert "butternut squash" in blob.lower()
        assert "fall" in blob.lower()

    def test_handles_missing_and_string_keywords(self) -> None:
        """Missing ingredients and string keywords don't raise."""
        assert seasonal_model.recipe_text({"title": "X", "keywords": "summer"})
        assert seasonal_model.recipe_text({}) == ""
