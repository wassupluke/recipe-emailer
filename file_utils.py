"""File utilities for JSON handling and file age checking."""

import json
import os
import time


def save_json(filename: str, data: dict) -> None:
    """Save JSON data to a file."""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def load_json(filename: str) -> tuple[dict, bool]:
    """Return dictionary of JSON data from a file and whether it was newly created.

    Returns:
        tuple: (data dict, was_created bool)
    """
    try:
        with open(filename) as f:
            data = json.load(f)
        return data, False
    except FileNotFoundError:
        print(f"Did not find {filename}, creating it now...")
        save_json(filename, {})
        return {}, True
    except json.JSONDecodeError:
        print(f"{filename} exists but is empty, initializing it now...")
        save_json(filename, {})
        return {}, True


def is_file_old(filename: str, old: int = 12, age: int = 12) -> bool:
    """Check if a file is older than a certain age."""
    if os.path.isfile(filename):  # check that the file exists
        age = int(os.stat(filename).st_mtime)
        age = int((time.time() - age) / 3600)  # convert seconds to hours
    return age >= old