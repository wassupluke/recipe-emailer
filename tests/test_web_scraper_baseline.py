"""Characterization tests for web_scraper module - locks in existing behavior."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from web_scraper import (
    PageResult,
    cleanup_recipe_urls,
    fetch_page,
    get_html,
    get_recipe_urls,
    scraper,
)


class TestGetHtml:
    """Test get_html function behavior."""

    @patch("web_scraper.requests.get")
    def test_successful_html_fetch(self, mock_get: Mock) -> None:
        """Test successful HTML retrieval."""
        mock_response = Mock()
        mock_response.text = "<html>test content</html>"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response

        result = get_html("https://example.com", debug_mode=False)

        assert result == "<html>test content</html>"
        mock_get.assert_called_once()

    @patch("web_scraper.requests.get")
    def test_timeout_returns_empty_string(self, mock_get: Mock) -> None:
        """Test that timeout returns empty string."""
        mock_get.side_effect = requests.exceptions.Timeout()

        result = get_html("https://example.com", debug_mode=False)

        assert result == ""

    @patch("web_scraper.requests.get")
    def test_debug_mode_uses_longer_timeout(self, mock_get: Mock) -> None:
        """Test that debug mode uses DEBUG_TIMEOUT."""
        mock_response = Mock()
        mock_response.text = "content"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response

        get_html("https://example.com", debug_mode=True)

        # Verify timeout parameter
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["timeout"] == 20  # DEBUG_TIMEOUT

    @patch("web_scraper.requests.get")
    def test_normal_mode_uses_normal_timeout(self, mock_get: Mock) -> None:
        """Test that normal mode uses NORMAL_TIMEOUT."""
        mock_response = Mock()
        mock_response.text = "content"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response

        get_html("https://example.com", debug_mode=False)

        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["timeout"] == 9  # NORMAL_TIMEOUT


class TestGetRecipeUrls:
    """Test get_recipe_urls function behavior."""

    @patch("web_scraper.fetch_page")
    def test_extracts_urls_and_reports_ok_status(self, mock_fetch):
        """Matched URLs are extracted and each course reports an OK status."""
        mock_fetch.side_effect = [
            PageResult(
                reachable=True,
                status_code=200,
                html='<a href="https://example.com/recipe1">',
            ),
            PageResult(
                reachable=True,
                status_code=200,
                html='<a href="https://example.com/side1">',
            ),
        ]
        selection = {
            "main course": "https://example.com/mains",
            "side dish": "https://example.com/sides",
            "regex": r'href="(https://example.com/\w+)"',
        }

        main_urls, side_urls, statuses = get_recipe_urls(selection, debug_mode=False)

        assert "https://example.com/recipe1" in main_urls
        assert "https://example.com/side1" in side_urls
        assert statuses["main course"] == ("OK", 1)
        assert statuses["side dish"] == ("OK", 1)

    @patch("web_scraper.fetch_page")
    def test_reachable_with_no_matches_reports_regex_broken(self, mock_fetch):
        """A reachable page yielding zero matches reports REGEX_BROKEN."""
        mock_fetch.side_effect = [
            PageResult(reachable=True, status_code=200, html="no matches here"),
            PageResult(reachable=True, status_code=200, html="no matches here"),
        ]
        selection = {
            "main course": "url1",
            "side dish": "url2",
            "regex": r'href="(https://nomatch.com/\w+)"',
        }

        main_urls, side_urls, statuses = get_recipe_urls(selection)

        assert main_urls == []
        assert side_urls == []
        assert statuses["main course"] == ("REGEX_BROKEN", 0)
        assert statuses["side dish"] == ("REGEX_BROKEN", 0)

    @patch("web_scraper.fetch_page")
    def test_unreachable_page_reports_unreachable_status(self, mock_fetch):
        """An unreachable page reports UNREACHABLE and yields no URLs."""
        mock_fetch.side_effect = [
            PageResult(reachable=False, status_code=None, html=""),
            PageResult(reachable=False, status_code=503, html=""),
        ]
        selection = {
            "main course": "url1",
            "side dish": "url2",
            "regex": r'href="(\S+)"',
        }

        main_urls, side_urls, statuses = get_recipe_urls(selection)

        assert main_urls == []
        assert side_urls == []
        assert statuses["main course"] == ("UNREACHABLE", 0)
        assert statuses["side dish"] == ("UNREACHABLE", 0)


class TestCleanupRecipeUrls:
    """Test cleanup_recipe_urls function behavior."""

    def test_fixes_relative_urls(self):
        """Test that relative URLs are fixed with domain."""
        urls = ["/recipes/test-recipe"]

        cleanup_recipe_urls(urls)

        assert urls[0] == "https://www.leanandgreenrecipes.net/recipes/test-recipe"

    def test_removes_urls_with_plan_keyword(self):
        """Test URLs containing 'plan' are removed."""
        urls = [
            "https://example.com/recipe",
            "https://example.com/meal-plan",
            "https://example.com/another-recipe",
        ]

        cleanup_recipe_urls(urls)

        assert len(urls) == 2
        assert "https://example.com/meal-plan" not in urls

    def test_removes_urls_with_eggplant(self):
        """Test URLs containing 'eggplant' are removed."""
        urls = ["https://example.com/recipe", "https://example.com/eggplant-parmesan"]

        cleanup_recipe_urls(urls)

        assert len(urls) == 1
        assert "https://example.com/eggplant-parmesan" not in urls

    def test_removes_multiple_keyword_patterns(self):
        """Test URLs matching multiple keyword patterns."""
        urls = [
            "https://example.com/dishes/recipes/best",
            "https://example.com/good-recipe",
            "https://example.com/black-friday-deals",
        ]

        cleanup_recipe_urls(urls)

        # First and third should be removed
        assert len(urls) == 1
        assert urls[0] == "https://example.com/good-recipe"

    def test_preserves_valid_urls(self):
        """Test that valid URLs are preserved."""
        original_urls = [
            "https://example.com/chicken-recipe",
            "https://example.com/salmon-dinner",
        ]
        urls = original_urls.copy()

        cleanup_recipe_urls(urls)

        assert urls == original_urls


class TestScrapeRecipe:
    """Test scraper function behavior."""

    @patch("web_scraper.scrape_html")
    def test_successful_scrape_returns_elements(self, mock_scrape: Mock) -> None:
        """Test successful recipe scraping."""
        mock_scrape_obj = Mock()
        mock_scrape_obj.to_json.return_value = {
            "canonical_url": "https://example.com/recipe",
            "title": "Test Recipe",
            "site_name": "Example",
            "host": "example.com",
            "ingredients": ["ingredient1", "ingredient2"],
            "instructions": "Do this and that",
            "image": "https://example.com/image.jpg",
        }
        mock_scrape.return_value = mock_scrape_obj

        failed_recipes: dict[str, str] = {}
        result = scraper(
            "<html>content</html>", "https://example.com/recipe", failed_recipes
        )

        assert result is not None
        assert result["title"] == "Test Recipe"
        assert len(failed_recipes) == 0

    @patch("web_scraper.scrape_html")
    def test_replaces_canonical_url_if_different(self, mock_scrape: Mock) -> None:
        """Test that canonical_url is replaced with input URL if different."""
        mock_scrape_obj = Mock()
        mock_scrape_obj.to_json.return_value = {
            "canonical_url": "https://different.com/recipe",
            "title": "Test",
            "site_name": "Site",
            "host": "host",
            "ingredients": ["ing"],
            "instructions": "inst",
            "image": "img.jpg",
        }
        mock_scrape.return_value = mock_scrape_obj

        failed_recipes: dict[str, str] = {}
        result = scraper("html", "https://example.com/recipe", failed_recipes)

        assert result is not None
        assert result["canonical_url"] == "https://example.com/recipe"

    @patch("web_scraper.scrape_html")
    def test_missing_required_key_adds_to_failed(self, mock_scrape: Mock) -> None:
        """Test that missing required keys cause failure."""
        mock_scrape_obj = Mock()
        mock_scrape_obj.to_json.return_value = {
            "canonical_url": "https://example.com/recipe",
            # Missing required keys
        }
        mock_scrape.return_value = mock_scrape_obj

        failed_recipes: dict[str, str] = {}
        result = scraper("html", "https://example.com/recipe", failed_recipes)

        assert result is None
        assert "https://example.com/recipe" in failed_recipes

    @patch("web_scraper.scrape_html")
    def test_empty_ingredients_adds_to_failed(self, mock_scrape: Mock) -> None:
        """Test that empty ingredients list causes failure."""
        mock_scrape_obj = Mock()
        mock_scrape_obj.to_json.return_value = {
            "canonical_url": "https://example.com/recipe",
            "title": "Test",
            "site_name": "Site",
            "host": "host",
            "ingredients": [],  # Empty
            "instructions": "inst",
            "image": "img",
        }
        mock_scrape.return_value = mock_scrape_obj

        failed_recipes: dict[str, str] = {}
        result = scraper("html", "https://example.com/recipe", failed_recipes)

        assert result is None
        assert "https://example.com/recipe" in failed_recipes

    @patch("web_scraper.scrape_html")
    def test_blank_instructions_adds_to_failed(self, mock_scrape: Mock) -> None:
        """Test that blank instructions cause failure."""
        mock_scrape_obj = Mock()
        mock_scrape_obj.to_json.return_value = {
            "canonical_url": "https://example.com/recipe",
            "title": "Test",
            "site_name": "Site",
            "host": "host",
            "ingredients": ["ing"],
            "instructions": "",  # Blank
            "image": "img",
        }
        mock_scrape.return_value = mock_scrape_obj

        failed_recipes: dict[str, str] = {}
        result = scraper("html", "https://example.com/recipe", failed_recipes)

        assert result is None
        assert "https://example.com/recipe" in failed_recipes

    @patch("web_scraper.scrape_html")
    def test_none_image_adds_to_failed(self, mock_scrape: Mock) -> None:
        """Test that None image causes failure."""
        mock_scrape_obj = Mock()
        mock_scrape_obj.to_json.return_value = {
            "canonical_url": "https://example.com/recipe",
            "title": "Test",
            "site_name": "Site",
            "host": "host",
            "ingredients": ["ing"],
            "instructions": "inst",
            "image": None,  # None
        }
        mock_scrape.return_value = mock_scrape_obj

        failed_recipes: dict[str, str] = {}
        result = scraper("html", "https://example.com/recipe", failed_recipes)

        assert result is None
        assert "https://example.com/recipe" in failed_recipes

    @patch("web_scraper.scrape_html")
    def test_exception_adds_to_failed_and_returns_none(self, mock_scrape: Mock) -> None:
        """Test that exceptions are caught and recipe added to failed."""
        mock_scrape.side_effect = Exception("Scraping error")

        failed_recipes: dict[str, str] = {}
        result = scraper("html", "https://example.com/recipe", failed_recipes)

        assert result is None
        assert "https://example.com/recipe" in failed_recipes
        assert "Scraping error" in failed_recipes["https://example.com/recipe"]


class TestFetchPage:
    """Test fetch_page reachability classification."""

    @patch("web_scraper.requests.get")
    def test_reachable_on_200_with_body(self, mock_get: Mock) -> None:
        """A 200 response with a non-empty body is classified as reachable."""
        mock_response = Mock()
        mock_response.text = "<html>content</html>"
        mock_response.status_code = 200
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response

        result = fetch_page("https://example.com")

        assert result == PageResult(
            reachable=True, status_code=200, html="<html>content</html>"
        )

    @patch("web_scraper.requests.get")
    def test_unreachable_on_200_with_empty_body(self, mock_get: Mock) -> None:
        """A 200 response with a blank body is classified as unreachable."""
        mock_response = Mock()
        mock_response.text = "   "
        mock_response.status_code = 200
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response

        result = fetch_page("https://example.com")

        assert result.reachable is False
        assert result.status_code == 200

    @patch("web_scraper.requests.get")
    def test_unreachable_on_non_200(self, mock_get: Mock) -> None:
        """A non-200 status code is classified as unreachable."""
        mock_response = Mock()
        mock_response.text = "Forbidden"
        mock_response.status_code = 403
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response

        result = fetch_page("https://example.com")

        assert result.reachable is False
        assert result.status_code == 403

    @patch("web_scraper.requests.get")
    def test_unreachable_on_timeout(self, mock_get: Mock) -> None:
        """A request timeout is classified as unreachable with no status code."""
        mock_get.side_effect = requests.exceptions.Timeout()

        result = fetch_page("https://example.com")

        assert result == PageResult(reachable=False, status_code=None, html="")

    @patch("web_scraper.requests.get")
    def test_unreachable_on_connection_error(self, mock_get: Mock) -> None:
        """A connection error is classified as unreachable with no status code."""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        result = fetch_page("https://example.com")

        assert result.reachable is False
        assert result.status_code is None
