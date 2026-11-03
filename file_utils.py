"""File utilities for JSON handling and file age checking.

This module provides functions for saving and loading JSON files,
as well as checking file age for cache invalidation.
"""

from __future__ import annotations

import json
import logging
import os
import stat
import tempfile
import time
from pathlib import Path
from typing import Any, TypeAlias

__all__ = ["save_json", "load_json", "is_file_old", "FileLoadResult"]

# Type alias for clarity
FileLoadResult: TypeAlias = tuple[dict[str, Any], bool]

logger = logging.getLogger(__name__)


class FileOperationError(Exception):
    """Raised when a file operation fails."""

    pass


def save_json(filepath: str | Path, data: dict[str, Any]) -> None:
    """Save dictionary data to a JSON file with pretty formatting.

    The write is atomic: data goes to a temp file in the same directory, which
    then replaces the target in one step. A crash or power loss mid-save leaves
    the old file intact instead of a truncated one (which load_json would
    otherwise treat as invalid and reset to {}).

    Args:
        filepath: Path to the file where data should be saved
        data: Dictionary to serialize to JSON

    Raises:
        FileOperationError: If the file cannot be written

    Example:
        >>> save_json("recipes.json", {"recipe1": {"title": "Pasta"}})
    """
    filepath = Path(filepath)
    tmp_path: Path | None = None

    try:
        # Same directory as the target, so os.replace stays on one filesystem
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=filepath.parent,
            prefix=f".{filepath.name}.",
            suffix=".tmp",
            delete=False,
        ) as f:
            tmp_path = Path(f.name)
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        # Temp files are created owner-only (0600); keep the old file's mode
        mode = stat.S_IMODE(filepath.stat().st_mode) if filepath.exists() else 0o644
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, filepath)
        logger.debug(f"Saved {len(data)} items to {filepath}")
    except (OSError, TypeError, ValueError) as e:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
        logger.error(f"Failed to save JSON to {filepath}: {e}")
        raise FileOperationError(f"Could not save to {filepath}") from e


def load_json(filepath: str | Path) -> FileLoadResult:
    """Load dictionary from a JSON file, creating it if it doesn't exist.

    Args:
        filepath: Path to the JSON file to load

    Returns:
        Tuple of (data dictionary, was_created boolean)
        - data: The loaded dictionary (empty dict if file was created/invalid)
        - was_created: True if file was just created or reinitialized

    Example:
        >>> data, created = load_json("recipes.json")
        >>> if created:
        ...     print("File was newly created")
    """
    filepath = Path(filepath)

    try:
        with filepath.open("r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"Loaded {len(data)} items from {filepath}")
        return data, False

    except FileNotFoundError:
        logger.info(f"File {filepath} not found, creating it...")
        save_json(filepath, {})
        return {}, True

    except json.JSONDecodeError:
        logger.warning(f"File {filepath} contains invalid JSON, reinitializing...")
        save_json(filepath, {})
        return {}, True

    except OSError as e:
        logger.error(f"Error reading {filepath}: {e}")
        # Still create the file for consistency
        save_json(filepath, {})
        return {}, True


def is_file_old(filepath: str | Path, threshold_hours: int = 12) -> bool:
    """Check if a file is older than a specified age in hours.

    Args:
        filepath: Path to the file to check
        threshold_hours: Age threshold in hours (default: 12)

    Returns:
        True if file is older than threshold or doesn't exist,
        False otherwise

    Example:
        >>> if is_file_old("cache.json", threshold_hours=24):
        ...     print("Cache is stale, refresh needed")
    """
    filepath = Path(filepath)

    if not filepath.exists():
        logger.debug(f"File {filepath} doesn't exist, considered old")
        return True

    try:
        modification_time = filepath.stat().st_mtime
        age_seconds = time.time() - modification_time
        age_hours = int(age_seconds / 3600)

        is_old = age_hours >= threshold_hours
        logger.debug(
            f"File {filepath} is {age_hours} hours old "
            f"(threshold: {threshold_hours})"
        )
        return is_old

    except OSError as e:
        logger.error(f"Error checking age of {filepath}: {e}")
        return True
