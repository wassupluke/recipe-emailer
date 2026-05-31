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
    def test_respects_cap(self, mock_tag, mock_save):
        """Respects cap."""
        mock_tag.return_value = True
        # 60 mains, cap is 50 -> only 50 tag attempts
        context = {
            "unused_mains": {f"u{i}": {"title": str(i)} for i in range(60)},
            "unused_sides": {},
        }

        with patch("main.SEASONAL_TAG_MAX_PER_RUN", 50):
            main._tag_new_recipes(context)

        assert mock_tag.call_count == 50

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
