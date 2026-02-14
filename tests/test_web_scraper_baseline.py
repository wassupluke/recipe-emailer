"""Characterization tests for web_scraper module - locks in existing behavior."""

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from web_scraper import get_html, get_recipe_urls, cleanup_recipe_urls, scrape_recipe


class TestGetHtml:
    """Test get_html function behavior."""

    @patch('web_scraper.requests.get')
    def test_successful_html_fetch(self, mock_get):
        """Test successful HTML retrieval."""
        mock_response = Mock()
        mock_response.text = "<html>test content</html>"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response
        
        result = get_html("https://example.com", debug_mode=False)
        
        assert result == "<html>test content</html>"
        mock_get.assert_called_once()

    @patch('web_scraper.requests.get')
    def test_timeout_returns_empty_string(self, mock_get):
        """Test that timeout returns empty string."""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        result = get_html("https://example.com", debug_mode=False)
        
        assert result == ""

    @patch('web_scraper.requests.get')
    def test_debug_mode_uses_longer_timeout(self, mock_get):
        """Test that debug mode uses DEBUG_TIMEOUT."""
        mock_response = Mock()
        mock_response.text = "content"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response
        
        get_html("https://example.com", debug_mode=True)
        
        # Verify timeout parameter
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs['timeout'] == 20  # DEBUG_TIMEOUT

    @patch('web_scraper.requests.get')
    def test_normal_mode_uses_normal_timeout(self, mock_get):
        """Test that normal mode uses NORMAL_TIMEOUT."""
        mock_response = Mock()
        mock_response.text = "content"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response
        
        get_html("https://example.com", debug_mode=False)
        
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs['timeout'] == 9  # NORMAL_TIMEOUT


class TestGetRecipeUrls:
    """Test get_recipe_urls function behavior."""

    @patch('web_scraper.get_html')
    def test_extracts_urls_from_both_pages(self, mock_get_html):
        """Test URL extraction from main and side pages."""
        mock_get_html.side_effect = [
            '<a href="https://example.com/recipe1">',
            '<a href="https://example.com/side1">'
        ]
        
        selection = {
            "main course": "https://example.com/mains",
            "side dish": "https://example.com/sides",
            "regex": r'href="(https://example.com/\w+)"'
        }
        
        main_urls, side_urls = get_recipe_urls(selection, debug_mode=False)
        
        assert "https://example.com/recipe1" in main_urls
        assert "https://example.com/side1" in side_urls

    @patch('web_scraper.get_html')
    def test_returns_empty_lists_on_no_match(self, mock_get_html):
        """Test returns empty lists when regex doesn't match."""
        mock_get_html.side_effect = ["no matches here", "no matches here"]
        
        selection = {
            "main course": "url1",
            "side dish": "url2",
            "regex": r'href="(https://nomatch.com/\w+)"'
        }
        
        main_urls, side_urls = get_recipe_urls(selection)
        
        assert main_urls == []
        assert side_urls == []


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
            "https://example.com/another-recipe"
        ]
        
        cleanup_recipe_urls(urls)
        
        assert len(urls) == 2
        assert "https://example.com/meal-plan" not in urls

    def test_removes_urls_with_eggplant(self):
        """Test URLs containing 'eggplant' are removed."""
        urls = [
            "https://example.com/recipe",
            "https://example.com/eggplant-parmesan"
        ]
        
        cleanup_recipe_urls(urls)
        
        assert len(urls) == 1
        assert "https://example.com/eggplant-parmesan" not in urls

    def test_removes_multiple_keyword_patterns(self):
        """Test URLs matching multiple keyword patterns."""
        urls = [
            "https://example.com/dishes/recipes/best",
            "https://example.com/good-recipe",
            "https://example.com/black-friday-deals"
        ]
        
        cleanup_recipe_urls(urls)
        
        # First and third should be removed
        assert len(urls) == 1
        assert urls[0] == "https://example.com/good-recipe"

    def test_preserves_valid_urls(self):
        """Test that valid URLs are preserved."""
        original_urls = [
            "https://example.com/chicken-recipe",
            "https://example.com/salmon-dinner"
        ]
        urls = original_urls.copy()
        
        cleanup_recipe_urls(urls)
        
        assert urls == original_urls


class TestScrapeRecipe:
    """Test scraper function behavior."""

    @patch('web_scraper.scrape_html')
    def test_successful_scrape_returns_elements(self, mock_scrape):
        """Test successful recipe scraping."""
        mock_scrape_obj = Mock()
        mock_scrape_obj.to_json.return_value = {
            "canonical_url": "https://example.com/recipe",
            "title": "Test Recipe",
            "site_name": "Example",
            "host": "example.com",
            "ingredients": ["ingredient1", "ingredient2"],
            "instructions": "Do this and that",
            "image": "https://example.com/image.jpg"
        }
        mock_scrape.return_value = mock_scrape_obj
        
        failed_recipes = {}
        result = scrape_recipe("<html>content</html>", "https://example.com/recipe", failed_recipes)
        
        assert result is not None
        assert result["title"] == "Test Recipe"
        assert len(failed_recipes) == 0

    @patch('web_scraper.scrape_html')
    def test_replaces_canonical_url_if_different(self, mock_scrape):
        """Test that canonical_url is replaced with input URL if different."""
        mock_scrape_obj = Mock()
        mock_scrape_obj.to_json.return_value = {
            "canonical_url": "https://different.com/recipe",
            "title": "Test",
            "site_name": "Site",
            "host": "host",
            "ingredients": ["ing"],
            "instructions": "inst",
            "image": "img.jpg"
        }
        mock_scrape.return_value = mock_scrape_obj
        
        failed_recipes = {}
        result = scrape_recipe("html", "https://example.com/recipe", failed_recipes)
        
        assert result["canonical_url"] == "https://example.com/recipe"

    @patch('web_scraper.scrape_html')
    def test_missing_required_key_adds_to_failed(self, mock_scrape):
        """Test that missing required keys cause failure."""
        mock_scrape_obj = Mock()
        mock_scrape_obj.to_json.return_value = {
            "canonical_url": "https://example.com/recipe",
            # Missing required keys
        }
        mock_scrape.return_value = mock_scrape_obj
        
        failed_recipes = {}
        result = scrape_recipe("html", "https://example.com/recipe", failed_recipes)
        
        assert result is None
        assert "https://example.com/recipe" in failed_recipes

    @patch('web_scraper.scrape_html')
    def test_empty_ingredients_adds_to_failed(self, mock_scrape):
        """Test that empty ingredients list causes failure."""
        mock_scrape_obj = Mock()
        mock_scrape_obj.to_json.return_value = {
            "canonical_url": "https://example.com/recipe",
            "title": "Test",
            "site_name": "Site",
            "host": "host",
            "ingredients": [],  # Empty
            "instructions": "inst",
            "image": "img"
        }
        mock_scrape.return_value = mock_scrape_obj
        
        failed_recipes = {}
        result = scrape_recipe("html", "https://example.com/recipe", failed_recipes)
        
        assert result is None
        assert "https://example.com/recipe" in failed_recipes

    @patch('web_scraper.scrape_html')
    def test_blank_instructions_adds_to_failed(self, mock_scrape):
        """Test that blank instructions cause failure."""
        mock_scrape_obj = Mock()
        mock_scrape_obj.to_json.return_value = {
            "canonical_url": "https://example.com/recipe",
            "title": "Test",
            "site_name": "Site",
            "host": "host",
            "ingredients": ["ing"],
            "instructions": "",  # Blank
            "image": "img"
        }
        mock_scrape.return_value = mock_scrape_obj
        
        failed_recipes = {}
        result = scrape_recipe("html", "https://example.com/recipe", failed_recipes)
        
        assert result is None
        assert "https://example.com/recipe" in failed_recipes

    @patch('web_scraper.scrape_html')
    def test_none_image_adds_to_failed(self, mock_scrape):
        """Test that None image causes failure."""
        mock_scrape_obj = Mock()
        mock_scrape_obj.to_json.return_value = {
            "canonical_url": "https://example.com/recipe",
            "title": "Test",
            "site_name": "Site",
            "host": "host",
            "ingredients": ["ing"],
            "instructions": "inst",
            "image": None  # None
        }
        mock_scrape.return_value = mock_scrape_obj
        
        failed_recipes = {}
        result = scrape_recipe("html", "https://example.com/recipe", failed_recipes)
        
        assert result is None
        assert "https://example.com/recipe" in failed_recipes

    @patch('web_scraper.scrape_html')
    def test_exception_adds_to_failed_and_returns_none(self, mock_scrape):
        """Test that exceptions are caught and recipe added to failed."""
        mock_scrape.side_effect = Exception("Scraping error")
        
        failed_recipes = {}
        result = scrape_recipe("html", "https://example.com/recipe", failed_recipes)
        
        assert result is None
        assert "https://example.com/recipe" in failed_recipes
        assert "Scraping error" in failed_recipes["https://example.com/recipe"]
