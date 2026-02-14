"""Comprehensive tests for refactored file_utils module."""

import json
import os
import tempfile
import time
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_utils import (
    FileOperationError,
    load_json,
    save_json,
    is_file_old,
)


class TestSaveJson:
    """Test save_json function with edge cases."""

    def test_saves_empty_dict(self, tmp_path):
        """Test saving empty dictionary."""
        filepath = tmp_path / "test.json"
        save_json(filepath, {})
        
        assert filepath.exists()
        with filepath.open() as f:
            assert json.load(f) == {}

    def test_saves_nested_structure(self, tmp_path):
        """Test saving complex nested structures."""
        filepath = tmp_path / "nested.json"
        data = {
            "recipes": {
                "url1": {"title": "Recipe 1", "ingredients": ["a", "b"]},
                "url2": {"title": "Recipe 2", "nested": {"deep": "value"}},
            }
        }
        
        save_json(filepath, data)
        
        with filepath.open() as f:
            loaded = json.load(f)
        assert loaded == data

    def test_handles_unicode(self, tmp_path):
        """Test Unicode characters are preserved."""
        filepath = tmp_path / "unicode.json"
        data = {"text": "Café façade naïve Köln 北京 🍕"}
        
        save_json(filepath, data)
        
        with filepath.open() as f:
            loaded = json.load(f)
        assert loaded == data

    def test_raises_on_invalid_path(self, tmp_path):
        """Test error handling for invalid paths."""
        # Try to write to a path that can't exist
        invalid_path = tmp_path / "nonexistent" / "deep" / "path" / "file.json"
        
        with pytest.raises(FileOperationError):
            save_json(invalid_path, {})

    def test_accepts_string_or_path(self, tmp_path):
        """Test that both str and Path arguments work."""
        data = {"key": "value"}
        
        # Test with Path
        path_obj = tmp_path / "path_test.json"
        save_json(path_obj, data)
        assert path_obj.exists()
        
        # Test with str
        str_path = str(tmp_path / "str_test.json")
        save_json(str_path, data)
        assert Path(str_path).exists()


class TestLoadJson:
    """Test load_json function with various scenarios."""

    def test_loads_valid_json(self, tmp_path):
        """Test loading valid JSON file."""
        filepath = tmp_path / "valid.json"
        data = {"key": "value", "number": 42}
        with filepath.open("w") as f:
            json.dump(data, f)
        
        loaded, created = load_json(filepath)
        
        assert loaded == data
        assert created is False

    def test_creates_missing_file(self, tmp_path):
        """Test that missing file is created."""
        filepath = tmp_path / "missing.json"
        
        loaded, created = load_json(filepath)
        
        assert loaded == {}
        assert created is True
        assert filepath.exists()

    def test_handles_corrupt_json(self, tmp_path):
        """Test handling of corrupted JSON."""
        filepath = tmp_path / "corrupt.json"
        with filepath.open("w") as f:
            f.write('{"incomplete": }')
        
        loaded, created = load_json(filepath)
        
        assert loaded == {}
        assert created is True

    def test_handles_empty_file(self, tmp_path):
        """Test handling of empty file."""
        filepath = tmp_path / "empty.json"
        filepath.touch()
        
        loaded, created = load_json(filepath)
        
        assert loaded == {}
        assert created is True

    def test_preserves_data_types(self, tmp_path):
        """Test that various data types are preserved."""
        filepath = tmp_path / "types.json"
        data = {
            "string": "text",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "none": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
        }
        with filepath.open("w") as f:
            json.dump(data, f)
        
        loaded, _ = load_json(filepath)
        
        assert loaded == data
        assert isinstance(loaded["integer"], int)
        assert isinstance(loaded["float"], float)
        assert isinstance(loaded["boolean"], bool)


class TestIsFileOld:
    """Test is_file_old function with various conditions."""

    def test_fresh_file_not_old(self, tmp_path):
        """Test that recently created file is not old."""
        filepath = tmp_path / "fresh.json"
        filepath.touch()
        
        assert is_file_old(filepath, threshold_hours=1) is False

    def test_old_file_detected(self, tmp_path):
        """Test that old file is correctly identified."""
        filepath = tmp_path / "old.json"
        filepath.touch()
        
        # Set modification time to 25 hours ago
        old_time = time.time() - (25 * 3600)
        os.utime(filepath, (old_time, old_time))
        
        assert is_file_old(filepath, threshold_hours=24) is True

    def test_exact_threshold(self, tmp_path):
        """Test behavior at exact threshold."""
        filepath = tmp_path / "threshold.json"
        filepath.touch()
        
        # Set to exactly 12 hours ago
        threshold_time = time.time() - (12 * 3600)
        os.utime(filepath, (threshold_time, threshold_time))
        
        # Should be considered old (>= comparison)
        assert is_file_old(filepath, threshold_hours=12) is True

    def test_nonexistent_file(self, tmp_path):
        """Test that nonexistent file is considered old."""
        filepath = tmp_path / "nonexistent.json"
        
        assert is_file_old(filepath, threshold_hours=1) is True

    def test_custom_threshold(self, tmp_path):
        """Test custom threshold values."""
        filepath = tmp_path / "test.json"
        filepath.touch()
        
        # Set to 5 hours old
        time_5h_ago = time.time() - (5 * 3600)
        os.utime(filepath, (time_5h_ago, time_5h_ago))
        
        assert is_file_old(filepath, threshold_hours=4) is True
        assert is_file_old(filepath, threshold_hours=6) is False

    def test_accepts_string_or_path(self, tmp_path):
        """Test that both str and Path work."""
        filepath = tmp_path / "test.json"
        filepath.touch()
        
        # Both should work identically
        result_path = is_file_old(filepath, threshold_hours=1)
        result_str = is_file_old(str(filepath), threshold_hours=1)
        
        assert result_path == result_str == False


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_save_load_roundtrip(self, tmp_path):
        """Test that save and load are symmetric."""
        filepath = tmp_path / "roundtrip.json"
        original_data = {
            "recipes": [
                {"id": 1, "name": "Test"},
                {"id": 2, "name": "Another"},
            ]
        }
        
        save_json(filepath, original_data)
        loaded_data, _ = load_json(filepath)
        
        assert loaded_data == original_data

    def test_large_file(self, tmp_path):
        """Test handling of large JSON files."""
        filepath = tmp_path / "large.json"
        # Create a large nested structure
        large_data = {f"key_{i}": {"data": list(range(100))} for i in range(1000)}
        
        save_json(filepath, large_data)
        loaded, _ = load_json(filepath)
        
        assert len(loaded) == 1000
        assert loaded == large_data
