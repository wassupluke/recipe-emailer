"""Tests for main._tag_new_recipes inline weekly tagging."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
import main


class TestTagNewRecipes:
    """Tests for tag new recipes."""

    @patch("main.save_json")
    @patch("main.ensure_recipe_tagged")
    def test_tags_untagged_and_saves(self, mock_tag, mock_save):
        """Tags untagged and saves."""
        mock_tag.return_value = True  # pretend each recipe got tagged
        context = {
            "unused_mains": {"u1": {"title": "A"}},
            "unused_sides": {"u2": {"title": "B"}},
        }

        main._tag_new_recipes(context)

        assert mock_tag.call_count == 2
        assert mock_save.call_count == 2  # mains + sides saved

    @patch("main.save_json")
    @patch("main.ensure_recipe_tagged")
    def test_tags_all_untagged_no_cap(self, mock_tag, mock_save):
        """Tags every untagged recipe in one run (no per-run cap)."""

        def fake_tag(recipe):
            recipe["seasonality"] = "summer"
            return True

        mock_tag.side_effect = fake_tag
        # 60 mains: with no cap, all 60 get tagged in a single run.
        context = {
            "unused_mains": {f"u{i}": {"title": str(i)} for i in range(60)},
            "unused_sides": {},
        }

        main._tag_new_recipes(context)

        assert mock_tag.call_count == 60
        assert all("seasonality" in r for r in context["unused_mains"].values())

    @patch("main.save_json")
    @patch("main.ensure_recipe_tagged")
    def test_never_raises_on_failure(self, mock_tag, mock_save):
        """Never raises on failure."""
        mock_tag.side_effect = RuntimeError("ollama exploded")
        context = {"unused_mains": {"u1": {"title": "A"}}, "unused_sides": {}}

        # Must swallow, not propagate
        main._tag_new_recipes(context)

    @patch("main.save_json")
    @patch("main.ensure_recipe_tagged")
    def test_no_save_when_nothing_changed(self, mock_tag, mock_save):
        """No save when nothing changed."""
        mock_tag.return_value = False  # already tagged
        context = {"unused_mains": {"u1": {"title": "A"}}, "unused_sides": {}}

        main._tag_new_recipes(context)

        mock_save.assert_not_called()
