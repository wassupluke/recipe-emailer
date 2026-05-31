"""Characterization tests for recipe_processor streaming scrape - locks in behavior."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
import recipe_processor


class TestScrapeFlushIntervalConfig:
    """Test the SCRAPE_FLUSH_INTERVAL config constant."""

    def test_flush_interval_default_value(self) -> None:
        """SCRAPE_FLUSH_INTERVAL defaults to 100 processed URLs."""
        assert config.SCRAPE_FLUSH_INTERVAL == 100

    def test_flush_interval_exported(self) -> None:
        """SCRAPE_FLUSH_INTERVAL is part of the config public API."""
        assert "SCRAPE_FLUSH_INTERVAL" in config.__all__


class TestFlushScrapeProgress:
    """Test the _flush_scrape_progress disk-persist helper."""

    @patch("recipe_processor.save_json")
    def test_flush_writes_target_and_failed(self, mock_save: Mock) -> None:
        """A flush persists the active stream's file plus the failed-recipes file."""
        target = {"u1": {"title": "a"}}
        failed = {"bad": "reason"}
        recipe_processor._flush_scrape_progress(
            config.UNUSED_MAINS_FILENAME, target, failed, debug_mode=False
        )
        # Writes exactly the active stream's file + the failed-recipes file.
        assert mock_save.call_count == 2
        mock_save.assert_any_call(config.UNUSED_MAINS_FILENAME, target)
        mock_save.assert_any_call(config.FAILED_FILENAME, failed)

    @patch("recipe_processor.save_json")
    def test_flush_is_noop_in_debug_mode(self, mock_save: Mock) -> None:
        """Debug mode never writes the database files."""
        recipe_processor._flush_scrape_progress(
            config.UNUSED_MAINS_FILENAME, {"u1": {}}, {}, debug_mode=True
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
        """Scraped recipes land in the target dict; failed (None) scrapes do not."""
        mock_get_html.side_effect = lambda url, dbg: f"html-{url}"
        # u2 fails to scrape (returns None); u1, u3 succeed.
        mock_scraper.side_effect = lambda html, url, failed: (
            None if url == "u2" else {"title": url}
        )
        target: dict[str, dict] = {}
        failed: dict[str, str] = {}

        recipe_processor._scrape_urls_streaming(
            ["u1", "u2", "u3"], target, config.UNUSED_MAINS_FILENAME, failed, False
        )

        assert target == {"u1": {"title": "u1"}, "u3": {"title": "u3"}}
        assert "u2" not in target

    @patch("recipe_processor.save_json")
    @patch("recipe_processor.scraper")
    @patch("recipe_processor.get_html")
    def test_streams_one_call_per_url(
        self, mock_get_html: Mock, mock_scraper: Mock, mock_save: Mock
    ) -> None:
        """Each URL triggers exactly one get_html and one scraper call (no batching)."""
        mock_get_html.return_value = "html"
        mock_scraper.return_value = {"title": "x"}
        urls = [f"u{i}" for i in range(7)]

        recipe_processor._scrape_urls_streaming(
            urls, {}, config.UNUSED_MAINS_FILENAME, {}, False
        )

        assert mock_get_html.call_count == 7
        assert mock_scraper.call_count == 7

    @patch("recipe_processor.save_json")
    @patch("recipe_processor.scraper")
    @patch("recipe_processor.get_html")
    def test_periodic_flush_plus_final(
        self, mock_get_html: Mock, mock_scraper: Mock, mock_save: Mock
    ) -> None:
        """Progress flushes every flush_interval URLs plus once at the end."""
        mock_get_html.return_value = "html"
        mock_scraper.return_value = {"title": "x"}

        recipe_processor._scrape_urls_streaming(
            [f"u{i}" for i in range(5)],
            {},
            config.UNUSED_MAINS_FILENAME,
            {},
            False,
            flush_interval=2,
        )

        # Flush after URLs 2 and 4, plus one final flush = 3 flushes.
        # Each flush writes target file + FAILED_FILENAME = 2 saves.
        target_saves = [
            c
            for c in mock_save.call_args_list
            if c.args[0] == config.UNUSED_MAINS_FILENAME
        ]
        failed_saves = [
            c for c in mock_save.call_args_list if c.args[0] == config.FAILED_FILENAME
        ]
        assert len(target_saves) == 3
        assert len(failed_saves) == 3

    @patch("recipe_processor.save_json")
    @patch("recipe_processor.scraper")
    @patch("recipe_processor.get_html")
    def test_final_flush_always_happens(
        self, mock_get_html: Mock, mock_scraper: Mock, mock_save: Mock
    ) -> None:
        """A single final flush occurs even when the interval is never hit."""
        mock_get_html.return_value = "html"
        mock_scraper.return_value = {"title": "x"}

        recipe_processor._scrape_urls_streaming(
            ["only"], {}, config.UNUSED_MAINS_FILENAME, {}, False, flush_interval=100
        )

        target_saves = [
            c
            for c in mock_save.call_args_list
            if c.args[0] == config.UNUSED_MAINS_FILENAME
        ]
        assert len(target_saves) == 1

    @patch("recipe_processor.save_json")
    @patch("recipe_processor.scraper")
    @patch("recipe_processor.get_html")
    def test_debug_mode_never_flushes(
        self, mock_get_html: Mock, mock_scraper: Mock, mock_save: Mock
    ) -> None:
        """Debug mode never persists progress, even past the flush interval."""
        mock_get_html.return_value = "html"
        mock_scraper.return_value = {"title": "x"}

        recipe_processor._scrape_urls_streaming(
            [f"u{i}" for i in range(5)],
            {},
            config.UNUSED_MAINS_FILENAME,
            {},
            True,
            flush_interval=2,
        )

        mock_save.assert_not_called()

    @patch("recipe_processor.save_json")
    @patch("recipe_processor.scraper")
    @patch("recipe_processor.get_html")
    def test_empty_url_list_still_flushes_once(
        self, mock_get_html: Mock, mock_scraper: Mock, mock_save: Mock
    ) -> None:
        """An empty URL list scrapes nothing but still does one final flush."""
        recipe_processor._scrape_urls_streaming(
            [], {}, config.UNUSED_MAINS_FILENAME, {}, False
        )

        mock_get_html.assert_not_called()
        mock_scraper.assert_not_called()
        target_saves = [
            c
            for c in mock_save.call_args_list
            if c.args[0] == config.UNUSED_MAINS_FILENAME
        ]
        failed_saves = [
            c for c in mock_save.call_args_list if c.args[0] == config.FAILED_FILENAME
        ]
        assert len(target_saves) == 1
        assert len(failed_saves) == 1

    @patch("recipe_processor.save_json")
    @patch("recipe_processor.scraper")
    @patch("recipe_processor.get_html")
    def test_get_html_error_on_one_url_does_not_abort_stream(
        self, mock_get_html: Mock, mock_scraper: Mock, mock_save: Mock
    ) -> None:
        """A get_html failure on one URL is recorded and the stream continues."""

        def _get_html(url: str, dbg: bool) -> str:
            if url == "u2":
                raise requests.exceptions.ConnectionError("boom")
            return "html"

        mock_get_html.side_effect = _get_html
        mock_scraper.side_effect = lambda html, url, failed: {"title": url}
        target: dict[str, dict] = {}
        failed: dict[str, str] = {}

        recipe_processor._scrape_urls_streaming(
            ["u1", "u2", "u3"], target, config.UNUSED_MAINS_FILENAME, failed, False
        )

        # u1 and u3 are still scraped despite u2 raising mid-stream.
        assert target == {"u1": {"title": "u1"}, "u3": {"title": "u3"}}
        # The failing URL is recorded so it is skipped on future runs.
        assert "u2" in failed
        # The final flush still ran.
        assert any(
            c.args[0] == config.UNUSED_MAINS_FILENAME for c in mock_save.call_args_list
        )


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
        """Mains and sides both stream; returns the 2-tuple and drops the DB repr."""
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
