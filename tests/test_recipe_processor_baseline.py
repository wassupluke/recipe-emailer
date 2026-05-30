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
