"""Characterization tests for debug_utils and html_generator modules."""

from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import pytest
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from debug_utils import is_debug_mode, select_website_interactively
from html_generator import generate_html_email


class TestIsDebugMode:
    """Test is_debug_mode function behavior."""

    @patch('sys.argv', ['script.py', '-d'])
    def test_detects_debug_flag(self):
        """Test that -d flag activates debug mode."""
        result = is_debug_mode()
        assert result is True

    @patch('sys.argv', ['script.py', '--debug'])
    def test_detects_debug_long_flag(self):
        """Test that --debug flag activates debug mode."""
        result = is_debug_mode()
        assert result is True

    @patch('sys.argv', ['script.py'])
    def test_no_debug_flag_returns_false(self):
        """Test that absence of debug flag returns False."""
        result = is_debug_mode()
        assert result is False


class TestSelectWebsiteInteractively:
    """Test select_website_interactively function behavior."""

    @patch('builtins.input', return_value='1')
    def test_valid_selection_returns_website(self, mock_input):
        """Test valid selection returns correct website data."""
        websites = {
            "Site1": {"url": "http://site1.com", "regex": "pattern1"},
            "Site2": {"url": "http://site2.com", "regex": "pattern2"}
        }
        
        result = select_website_interactively(websites)
        
        assert result == websites["Site1"]

    @patch('builtins.input', side_effect=['0', '5', 'abc', '1'])
    def test_invalid_inputs_retry_until_valid(self, mock_input):
        """Test that invalid inputs cause retry."""
        websites = {
            "Site1": {"url": "http://site1.com"}
        }
        
        result = select_website_interactively(websites)
        
        # Should eventually get valid input
        assert result == websites["Site1"]
        # Should have called input 4 times (3 invalid + 1 valid)
        assert mock_input.call_count == 4


class TestGenerateHtmlEmail:
    """Test prettify function behavior."""

    @patch('builtins.open', new_callable=mock_open, read_data='<head></head>')
    def test_generates_html_with_single_meal(self, mock_file):
        """Test HTML generation for single meal."""
        meals = [
            {
                "type": "single_main",
                "obj": {
                    "url1": {
                        "title": "Test Recipe",
                        "site_name": "Test Site",
                        "yields": "4 servings",
                        "image": "http://example.com/image.jpg",
                        "host": "example.com",
                        "ingredients": ["ingredient 1", "ingredient 2"],
                        "instructions": "Mix and cook"
                    }
                }
            }
        ]
        
        result = generate_html_email(meals, start_time=1.0, total_main_count=10, total_side_count=5)
        
        assert "</html>" in result  # Check for closing html tag
        assert "Test Recipe" in result
        assert "ingredient 1" in result
        assert "Mix and cook" in result

    @patch('builtins.open', new_callable=mock_open, read_data='<head></head>')
    def test_labels_combo_main_correctly(self, mock_file):
        """Test that combo_main meals are labeled as 'Main:'."""
        meals = [
            {
                "type": "combo_main",
                "obj": {
                    "url1": {
                        "title": "Chicken Dish",
                        "site_name": "Site",
                        "image": "img.jpg",
                        "host": "host.com",
                        "ingredients": ["chicken"],
                        "instructions": "Cook it"
                    }
                }
            }
        ]
        
        result = generate_html_email(meals, start_time=1.0, total_main_count=10, total_side_count=5)
        
        assert "Main: Chicken Dish" in result

    @patch('builtins.open', new_callable=mock_open, read_data='<head></head>')
    def test_labels_combo_side_correctly(self, mock_file):
        """Test that combo_side meals are labeled as 'Side:'."""
        meals = [
            {
                "type": "combo_side",
                "obj": {
                    "url1": {
                        "title": "Side Salad",
                        "site_name": "Site",
                        "image": "img.jpg",
                        "host": "host.com",
                        "ingredients": ["lettuce"],
                        "instructions": "Toss it"
                    }
                }
            }
        ]
        
        result = generate_html_email(meals, start_time=1.0, total_main_count=10, total_side_count=5)
        
        assert "Side: Side Salad" in result

    @patch('builtins.open', new_callable=mock_open, read_data='<head></head>')
    def test_handles_missing_yields(self, mock_file):
        """Test handling of recipes without yields field."""
        meals = [
            {
                "type": "single_main",
                "obj": {
                    "url1": {
                        "title": "Recipe",
                        "site_name": "Site",
                        # No yields field
                        "image": "img.jpg",
                        "host": "host.com",
                        "ingredients": ["ing"],
                        "instructions": "inst"
                    }
                }
            }
        ]
        
        result = generate_html_email(meals, start_time=1.0, total_main_count=10, total_side_count=5)
        
        assert "servings unknown" in result

    @patch('builtins.open', new_callable=mock_open, read_data='<head></head>')
    def test_includes_elapsed_time_in_seconds(self, mock_file):
        """Test elapsed time display for longer durations."""
        meals = [
            {
                "type": "single_main",
                "obj": {
                    "url1": {
                        "title": "Recipe",
                        "site_name": "Site",
                        "image": "img.jpg",
                        "host": "host.com",
                        "ingredients": ["ing"],
                        "instructions": "inst"
                    }
                }
            }
        ]
        
        # Start time 2 seconds ago
        import time
        start = time.time() - 2.0
        
        result = generate_html_email(meals, start_time=start, total_main_count=10, total_side_count=5)
        
        assert "seconds" in result

    @patch('builtins.open', new_callable=mock_open, read_data='<head></head>')
    def test_includes_elapsed_time_in_milliseconds(self, mock_file):
        """Test elapsed time display for short durations."""
        meals = [
            {
                "type": "single_main",
                "obj": {
                    "url1": {
                        "title": "Recipe",
                        "site_name": "Site",
                        "image": "img.jpg",
                        "host": "host.com",
                        "ingredients": ["ing"],
                        "instructions": "inst"
                    }
                }
            }
        ]
        
        # Start time 0.5 seconds ago
        import time
        start = time.time() - 0.5
        
        result = generate_html_email(meals, start_time=start, total_main_count=10, total_side_count=5)
        
        assert "ms" in result

    @patch('builtins.open', new_callable=mock_open, read_data='<head></head>')
    def test_includes_recipe_counts(self, mock_file):
        """Test that recipe counts are included in output."""
        meals = [
            {
                "type": "single_main",
                "obj": {
                    "url1": {
                        "title": "Recipe",
                        "site_name": "Site",
                        "image": "img.jpg",
                        "host": "host.com",
                        "ingredients": ["ing"],
                        "instructions": "inst"
                    }
                }
            }
        ]
        
        result = generate_html_email(meals, start_time=1.0, total_main_count=100, total_side_count=50)
        
        # Should show total: 100 + 50 = 150
        assert "150" in result
