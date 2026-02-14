"""Characterization tests for file_utils module - locks in existing behavior."""

import json
import os
import tempfile
import time
from pathlib import Path

import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from file_utils import save_json, load_json, is_file_old


class TestSaveJson:
    """Test save_json function behavior."""

    def test_saves_empty_dict(self, tmp_path):
        """Test saving an empty dictionary."""
        filepath = tmp_path / "test.json"
        data = {}
        
        save_json(str(filepath), data)
        
        assert filepath.exists()
        with open(filepath) as f:
            loaded = json.load(f)
        assert loaded == {}

    def test_saves_dict_with_data(self, tmp_path):
        """Test saving a dictionary with data."""
        filepath = tmp_path / "test.json"
        data = {"key1": "value1", "key2": ["list", "values"]}
        
        save_json(str(filepath), data)
        
        with open(filepath) as f:
            loaded = json.load(f)
        assert loaded == data

    def test_saves_with_indent(self, tmp_path):
        """Test that JSON is saved with indentation."""
        filepath = tmp_path / "test.json"
        data = {"key": "value"}
        
        save_json(str(filepath), data)
        
        with open(filepath) as f:
            content = f.read()
        # Should have newlines and spaces (indented)
        assert "\n" in content
        assert "  " in content

    def test_overwrites_existing_file(self, tmp_path):
        """Test that existing files are overwritten."""
        filepath = tmp_path / "test.json"
        old_data = {"old": "data"}
        new_data = {"new": "data"}
        
        save_json(str(filepath), old_data)
        save_json(str(filepath), new_data)
        
        with open(filepath) as f:
            loaded = json.load(f)
        assert loaded == new_data


class TestLoadJson:
    """Test load_json function behavior."""

    def test_loads_existing_file(self, tmp_path):
        """Test loading an existing JSON file."""
        filepath = tmp_path / "test.json"
        data = {"key": "value"}
        with open(filepath, "w") as f:
            json.dump(data, f)
        
        loaded_data, was_created = load_json(str(filepath))
        
        assert loaded_data == data
        assert was_created is False

    def test_creates_file_if_not_found(self, tmp_path):
        """Test that missing file is created and returns empty dict."""
        filepath = tmp_path / "missing.json"
        
        loaded_data, was_created = load_json(str(filepath))
        
        assert loaded_data == {}
        assert was_created is True
        assert filepath.exists()

    def test_handles_empty_file(self, tmp_path):
        """Test handling of existing but empty file."""
        filepath = tmp_path / "empty.json"
        filepath.touch()  # Create empty file
        
        loaded_data, was_created = load_json(str(filepath))
        
        assert loaded_data == {}
        assert was_created is True

    def test_handles_invalid_json(self, tmp_path):
        """Test handling of file with invalid JSON."""
        filepath = tmp_path / "invalid.json"
        with open(filepath, "w") as f:
            f.write("not valid json{")
        
        loaded_data, was_created = load_json(str(filepath))
        
        assert loaded_data == {}
        assert was_created is True


class TestIsFileOld:
    """Test is_file_old function behavior."""

    def test_new_file_is_not_old(self, tmp_path):
        """Test that a newly created file is not considered old."""
        filepath = tmp_path / "new.json"
        filepath.touch()
        
        result = is_file_old(str(filepath), threshold_hours=12)
        
        assert result is False

    def test_old_file_is_old(self, tmp_path):
        """Test that an old file is detected as old."""
        filepath = tmp_path / "old.json"
        filepath.touch()
        
        # Set modification time to 24 hours ago
        old_time = time.time() - (24 * 3600)
        os.utime(filepath, (old_time, old_time))
        
        result = is_file_old(str(filepath), threshold_hours=12)
        
        assert result is True

    def test_file_exactly_at_threshold(self, tmp_path):
        """Test file exactly at age threshold."""
        filepath = tmp_path / "threshold.json"
        filepath.touch()
        
        # Set to exactly 12 hours ago
        threshold_time = time.time() - (12 * 3600)
        os.utime(filepath, (threshold_time, threshold_time))
        
        result = is_file_old(str(filepath), threshold_hours=12)
        
        # Should be True (>= comparison)
        assert result is True

    def test_nonexistent_file_uses_default_age(self, tmp_path):
        """Test that nonexistent file returns using default age."""
        filepath = tmp_path / "nonexistent.json"
        
        result = is_file_old(str(filepath), threshold_hours=12)
        
        # Should use age parameter default (12) and return True
        assert result is True
