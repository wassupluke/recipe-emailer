#!/usr/bin/env python3
"""Desktop teacher: label recipes with seasonality scores via Ollama (GPU).

Run on the desktop with a GPU + Ollama serving a strong instruct model. Produces
seasonal_labels.json (url -> {spring,summer,fall,winter}) used to train the
student. Resumable: already-labeled urls are skipped.

    ollama pull llama3.1:8b
    python seasonal_label.py
"""

from __future__ import annotations

import json
import logging
from typing import Any

import requests
from tqdm import tqdm

from config import (
    OLLAMA_HOST,
    OLLAMA_TIMEOUT,
    SEASONAL_LABELS_FILENAME,
    SEASONAL_MODEL,
    UNUSED_MAINS_FILENAME,
    UNUSED_SIDES_FILENAME,
)
from file_utils import load_json, save_json

logger = logging.getLogger(__name__)

_SEASON_KEYS = ("spring", "summer", "fall", "winter")


def _build_prompt(title: str, ingredients: list[str]) -> str:
    """Build the seasonal-scoring prompt from a recipe's title + ingredients."""
    ingredient_lines = "\n".join(f"- {item}" for item in ingredients)
    return (
        "You rate how well a recipe fits each season in the Northern Hemisphere.\n"
        "Consider its ingredients' peak seasons and whether the dish feels "
        "light/cooling (summer) or warm/hearty (winter).\n"
        "Respond with ONLY a JSON object of four numbers from 0.0 to 1.0, keys "
        'exactly "spring", "summer", "fall", "winter".\n\n'
        f"Title: {title}\n"
        f"Ingredients:\n{ingredient_lines}\n"
    )


def _ollama_generate(prompt: str) -> str | None:
    """POST a prompt to Ollama; return the raw response string, or None on failure."""
    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": SEASONAL_MODEL,
                "prompt": prompt,
                "format": "json",
                "stream": False,
            },
            timeout=OLLAMA_TIMEOUT,
        )
        if resp.status_code != 200:
            logger.warning(f"Ollama returned status {resp.status_code}")
            return None
        data = resp.json()
        if not isinstance(data, dict):
            return None
        return str(data.get("response", ""))
    except requests.exceptions.RequestException as e:
        logger.warning(f"Ollama request failed: {e}")
        return None


def _parse_seasons(raw: str | None) -> dict[str, float] | None:
    """Parse + validate a seasonality JSON string; clamp to 0-1. None if invalid."""
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    result: dict[str, float] = {}
    for key in _SEASON_KEYS:
        if key not in data:
            return None
        value = data[key]
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return None
        result[key] = max(0.0, min(1.0, float(value)))
    return result


def _score_one(recipe: dict[str, Any]) -> dict[str, float] | None:
    """Score a single recipe via the teacher, retrying once."""
    prompt = _build_prompt(recipe.get("title", ""), recipe.get("ingredients", []))
    for _ in range(2):
        parsed = _parse_seasons(_ollama_generate(prompt))
        if parsed is not None:
            return parsed
    return None


def label_recipes(
    recipes: dict[str, dict[str, Any]], existing: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Return labels for all recipes, reusing existing labels (resumable)."""
    labels = dict(existing)
    for url, recipe in tqdm(recipes.items()):
        if url in labels:
            continue
        scored = _score_one(recipe)
        if scored is not None:
            labels[url] = scored
    return labels


def main() -> None:
    """Label the full recipe corpus and write SEASONAL_LABELS_FILENAME."""
    logging.basicConfig(level=logging.INFO)
    mains, _ = load_json(UNUSED_MAINS_FILENAME)
    sides, _ = load_json(UNUSED_SIDES_FILENAME)
    corpus = {**mains, **sides}
    try:
        existing, _ = load_json(SEASONAL_LABELS_FILENAME)
    except Exception:
        existing = {}
    labels = label_recipes(corpus, existing or {})
    save_json(SEASONAL_LABELS_FILENAME, labels)
    logger.info(f"Wrote {len(labels)} labels to {SEASONAL_LABELS_FILENAME}")


if __name__ == "__main__":
    main()
