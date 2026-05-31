"""Tests for the backfill_seasonality one-off script."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
import backfill_seasonality


class TestBackfillFile:
    """Tests for backfill file."""

    @patch("backfill_seasonality.save_json")
    @patch("backfill_seasonality.ensure_recipe_tagged")
    def test_tags_all_untagged_in_a_file(self, mock_tag, mock_save):
        """Tags all untagged in a file."""
        mock_tag.return_value = True
        recipes = {"u1": {"title": "A"}, "u2": {"title": "B"}, "u3": {"title": "C"}}

        tagged = backfill_seasonality.backfill_file(
            "some_file.json", recipes, save_every=2
        )

        assert mock_tag.call_count == 3
        assert tagged == 3
        # save_every=2 -> a save at recipe 2, plus a final save = 2 saves
        assert mock_save.call_count == 2

    @patch("backfill_seasonality.save_json")
    @patch("backfill_seasonality.ensure_recipe_tagged")
    def test_no_save_when_nothing_changed(self, mock_tag, mock_save):
        """No save when nothing changed."""
        mock_tag.return_value = False
        recipes = {"u1": {"title": "A"}}

        tagged = backfill_seasonality.backfill_file("f.json", recipes, save_every=25)

        assert tagged == 0
        mock_save.assert_not_called()
