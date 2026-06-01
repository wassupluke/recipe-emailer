"""Tests for the desktop teacher-labeling script."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
import seasonal_label


class TestParseSeasons:
    """Tests for _parse_seasons."""

    def test_valid_json_clamped(self) -> None:
        """Valid 4-key JSON is parsed and clamped to [0,1]."""
        out = seasonal_label._parse_seasons(
            '{"spring":0.2,"summer":1.5,"fall":0.0,"winter":-1}'
        )
        assert out == {"spring": 0.2, "summer": 1.0, "fall": 0.0, "winter": 0.0}

    def test_missing_key_returns_none(self) -> None:
        """A missing season key is invalid."""
        assert seasonal_label._parse_seasons('{"spring":0.2}') is None


class TestLabelRecipes:
    """Tests for label_recipes."""

    @patch("seasonal_label._ollama_generate")
    def test_labels_and_skips_existing(self, mock_gen) -> None:  # type: ignore[no-untyped-def]
        """Unlabeled recipes are scored; already-labeled urls are skipped."""
        mock_gen.return_value = '{"spring":0.1,"summer":0.9,"fall":0.0,"winter":0.0}'
        recipes = {
            "u1": {"title": "Gazpacho", "ingredients": ["tomato"]},
            "u2": {"title": "Stew", "ingredients": ["beef"]},
        }
        existing = {"u1": {"spring": 0, "summer": 1, "fall": 0, "winter": 0}}
        labels = seasonal_label.label_recipes(recipes, existing)
        assert set(labels) == {"u1", "u2"}
        assert mock_gen.call_count == 1  # only u2 needed scoring
        assert labels["u2"]["summer"] == 0.9
