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


class TestScrapeUrlsStreaming:
    """Test the _scrape_urls_streaming one-page-at-a-time loop."""

    @patch("recipe_processor.save_json")
    @patch("recipe_processor.scraper")
    @patch("recipe_processor.get_html")
    def test_routes_recipes_and_skips_none(
        self, mock_get_html: Mock, mock_scraper: Mock, mock_save: Mock
    ) -> None:
        mock_get_html.side_effect = lambda url, dbg: f"html-{url}"
        # u2 fails to scrape (returns None); u1, u3 succeed.
        mock_scraper.side_effect = lambda html, url, failed: (
            None if url == "u2" else {"title": url}
        )
        target: dict[str, dict] = {}
        failed: dict[str, str] = {}

        recipe_processor._scrape_urls_streaming(
            ["u1", "u2", "u3"], target, "unused_mains_recipes.json", failed, False
        )

        assert target == {"u1": {"title": "u1"}, "u3": {"title": "u3"}}
        assert "u2" not in target

    @patch("recipe_processor.save_json")
    @patch("recipe_processor.scraper")
    @patch("recipe_processor.get_html")
    def test_streams_one_call_per_url(
        self, mock_get_html: Mock, mock_scraper: Mock, mock_save: Mock
    ) -> None:
        mock_get_html.return_value = "html"
        mock_scraper.return_value = {"title": "x"}
        urls = [f"u{i}" for i in range(7)]

        recipe_processor._scrape_urls_streaming(
            urls, {}, "unused_mains_recipes.json", {}, False
        )

        assert mock_get_html.call_count == 7
        assert mock_scraper.call_count == 7

    @patch("recipe_processor.save_json")
    @patch("recipe_processor.scraper")
    @patch("recipe_processor.get_html")
    def test_periodic_flush_plus_final(
        self, mock_get_html: Mock, mock_scraper: Mock, mock_save: Mock
    ) -> None:
        mock_get_html.return_value = "html"
        mock_scraper.return_value = {"title": "x"}

        recipe_processor._scrape_urls_streaming(
            [f"u{i}" for i in range(5)],
            {},
            "unused_mains_recipes.json",
            {},
            False,
            flush_interval=2,
        )

        # Flush after URLs 2 and 4, plus one final flush = 3 flushes.
        # Each flush writes target file + FAILED_FILENAME = 2 saves.
        target_saves = [
            c for c in mock_save.call_args_list
            if c.args[0] == "unused_mains_recipes.json"
        ]
        failed_saves = [
            c for c in mock_save.call_args_list
            if c.args[0] == config.FAILED_FILENAME
        ]
        assert len(target_saves) == 3
        assert len(failed_saves) == 3

    @patch("recipe_processor.save_json")
    @patch("recipe_processor.scraper")
    @patch("recipe_processor.get_html")
    def test_final_flush_always_happens(
        self, mock_get_html: Mock, mock_scraper: Mock, mock_save: Mock
    ) -> None:
        mock_get_html.return_value = "html"
        mock_scraper.return_value = {"title": "x"}

        recipe_processor._scrape_urls_streaming(
            ["only"], {}, "unused_mains_recipes.json", {}, False, flush_interval=100
        )

        target_saves = [
            c for c in mock_save.call_args_list
            if c.args[0] == "unused_mains_recipes.json"
        ]
        assert len(target_saves) == 1

    @patch("recipe_processor.save_json")
    @patch("recipe_processor.scraper")
    @patch("recipe_processor.get_html")
    def test_debug_mode_never_flushes(
        self, mock_get_html: Mock, mock_scraper: Mock, mock_save: Mock
    ) -> None:
        mock_get_html.return_value = "html"
        mock_scraper.return_value = {"title": "x"}

        recipe_processor._scrape_urls_streaming(
            [f"u{i}" for i in range(5)],
            {},
            "unused_mains_recipes.json",
            {},
            True,
            flush_interval=2,
        )

        mock_save.assert_not_called()


class TestFetchFreshRecipesStreaming:
    """End-to-end: fetch_fresh_recipes streams mains then sides, no batch dicts."""

    @patch("recipe_processor.save_json")
    @patch("recipe_processor.scraper")
    @patch("recipe_processor.get_html")
    @patch("recipe_processor.get_recipe_urls")
    def test_streams_both_and_returns_two_tuple(
        self,
        mock_urls: Mock,
        mock_get_html: Mock,
        mock_scraper: Mock,
        mock_save: Mock,
        capsys,
    ) -> None:
        mock_urls.return_value = (["main1"], ["side1"])
        mock_get_html.return_value = "html"
        mock_scraper.side_effect = lambda html, url, failed: {"title": url}

        result = recipe_processor.fetch_fresh_recipes(
            websites={"site": {"url": "http://x"}},
            unused_main_recipes={},
            unused_side_recipes={},
            used_recipes={},
            failed_recipes={},
            debug_mode=False,
        )

        mains, sides = result
        assert mains == {"main1": {"title": "main1"}}
        assert sides == {"side1": {"title": "side1"}}
        # Whole-DB repr print is gone (no `unused_main_recipes=` dump).
        out = capsys.readouterr().out
        assert "unused_main_recipes=" not in out
        assert "unused_side_recipes=" not in out
