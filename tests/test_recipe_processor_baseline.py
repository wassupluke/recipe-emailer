"""Characterization tests for recipe_processor streaming scrape - locks in behavior."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
import recipe_processor


class TestScrapeFlushIntervalConfig:
    """Test the SCRAPE_FLUSH_INTERVAL config constant."""

    def test_flush_interval_default_value(self) -> None:
        assert config.SCRAPE_FLUSH_INTERVAL == 100

    def test_flush_interval_exported(self) -> None:
        assert "SCRAPE_FLUSH_INTERVAL" in config.__all__


class TestFlushScrapeProgress:
    """Test the _flush_scrape_progress disk-persist helper."""

    @patch("recipe_processor.save_json")
    def test_flush_writes_target_and_failed(self, mock_save: Mock) -> None:
        target = {"u1": {"title": "a"}}
        failed = {"bad": "reason"}
        recipe_processor._flush_scrape_progress(
            "unused_mains_recipes.json", target, failed, debug_mode=False
        )
        # Writes exactly the active stream's file + the failed-recipes file.
        assert mock_save.call_count == 2
        mock_save.assert_any_call("unused_mains_recipes.json", target)
        mock_save.assert_any_call(config.FAILED_FILENAME, failed)

    @patch("recipe_processor.save_json")
    def test_flush_is_noop_in_debug_mode(self, mock_save: Mock) -> None:
        recipe_processor._flush_scrape_progress(
            "unused_mains_recipes.json", {"u1": {}}, {}, debug_mode=True
        )
        mock_save.assert_not_called()
