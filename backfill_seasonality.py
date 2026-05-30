#!/usr/bin/env python3
"""One-off script: backfill seasonal/oven tags on the existing recipe backlog.

Run by hand once after installing Ollama and pulling the model:

    ollama pull qwen2.5:1.5b
    python backfill_seasonality.py

Safe to re-run: already-tagged recipes are skipped. Saves periodically so a long
run can be interrupted and resumed without losing progress.
"""

from __future__ import annotations

import logging
from typing import Any

from tqdm import tqdm

from config import UNUSED_MAINS_FILENAME, UNUSED_SIDES_FILENAME
from file_utils import load_json, save_json
from seasonal_tagging import ensure_recipe_tagged

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backfill_file(
    filename: str, recipes: dict[str, dict[str, Any]], save_every: int = 25
) -> int:
    """Tag every untagged recipe in `recipes`, saving every `save_every` changes.

    Returns the number of recipes newly tagged.
    """
    tagged = 0
    for recipe in tqdm(recipes.values(), desc=filename):
        if ensure_recipe_tagged(recipe):
            tagged += 1
            if tagged % save_every == 0:
                save_json(filename, recipes)
    if tagged:
        save_json(filename, recipes)
    return tagged


def main() -> None:
    """Backfill both unused recipe files and print a summary."""
    total = 0
    for filename in (UNUSED_MAINS_FILENAME, UNUSED_SIDES_FILENAME):
        recipes, _ = load_json(filename)
        tagged = backfill_file(filename, recipes)
        still_untagged = sum(1 for r in recipes.values() if "seasonality" not in r)
        logger.info(
            f"{filename}: tagged {tagged}, {still_untagged} still untagged "
            f"(model failures — re-run to retry)"
        )
        total += tagged
    logger.info(f"Backfill complete: {total} recipe(s) tagged.")


if __name__ == "__main__":
    main()
