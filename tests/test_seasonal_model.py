"""Tests for the pure-numpy distilled seasonality student model."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import seasonal_model


def _tiny_artifact(tmp_path: Path) -> str:
    """Write a 2-token artifact: 'summer'->summer=1, 'winter'->winter=1."""
    model = {
        "version": 1,
        "seasons": list(seasonal_model.SEASONS),
        "vocabulary": {"summer": 0, "winter": 1},
        "idf": [1.0, 1.0],
        # coef rows are [spring, summer, fall, winter] x [summer_col, winter_col]
        "coef": [[0.0, 0.0], [1.0, 0.0], [0.0, 0.0], [0.0, 1.0]],
        "intercept": [0.0, 0.0, 0.0, 0.0],
    }
    p = tmp_path / "seasonal_model.json"
    p.write_text(json.dumps(model))
    return str(p)


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


class TestPredictSeasons:
    """Tests for load_model + predict_seasons."""

    def test_predicts_from_artifact(self, tmp_path: Path) -> None:
        """A 'summer summer' blob scores summer highest, normalized + clamped."""
        model = seasonal_model.load_model(_tiny_artifact(tmp_path))
        scores = seasonal_model.predict_seasons("summer summer", model)
        assert set(scores) == set(seasonal_model.SEASONS)
        assert scores["summer"] == 1.0  # l2-normalized single-token vector
        assert scores["winter"] == 0.0
        assert all(0.0 <= v <= 1.0 for v in scores.values())

    def test_out_of_vocab_tokens_give_neutralish(self, tmp_path: Path) -> None:
        """Tokens absent from vocab yield a zero vector -> intercepts (0)."""
        model = seasonal_model.load_model(_tiny_artifact(tmp_path))
        scores = seasonal_model.predict_seasons("rutabaga", model)
        assert scores == {"spring": 0.0, "summer": 0.0, "fall": 0.0, "winter": 0.0}


class TestPredictForRecipe:
    """Tests for predict_for_recipe + fallback."""

    def test_missing_model_returns_neutral(self) -> None:
        """A missing artifact path yields the neutral 0.5 fallback, no raise."""
        scores = seasonal_model.predict_for_recipe(
            {"title": "x", "ingredients": ["y"]}, "/nonexistent/model.json"
        )
        assert scores == dict.fromkeys(seasonal_model.SEASONS, 0.5)

    def test_empty_recipe_returns_neutral(self, tmp_path: Path) -> None:
        """A recipe with no text yields neutral 0.5 without raising."""
        path = _tiny_artifact(tmp_path)
        assert seasonal_model.predict_for_recipe({}, path) == dict.fromkeys(
            seasonal_model.SEASONS, 0.5
        )
