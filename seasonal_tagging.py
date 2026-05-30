"""Produce cached seasonal + oven-use tags for recipes.

oven_use is rule-based (deterministic keyword scan). seasonality is produced by
a small local LLM via Ollama. All LLM/network failure is best-effort: callers
get None / unchanged recipes rather than exceptions.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import requests

from config import OLLAMA_HOST, OLLAMA_TIMEOUT, SEASONAL_MODEL

logger = logging.getLogger(__name__)

__all__ = [
    "score_oven_use",
    "score_seasons",
    "ensure_recipe_tagged",
]

_SEASON_KEYS = ("spring", "summer", "fall", "winter")

# Keyword groups for oven_use, checked in priority order: oven > grill/no-cook > stovetop.
_OVEN_KEYWORDS = (
    "oven",
    "bake",
    "baked",
    "baking",
    "roast",
    "broil",
    "350",
    "375",
    "400",
    "425",
    "450",
    "°f",
)
_NO_OVEN_KEYWORDS = (
    "grill",
    "grilled",
    "no-cook",
    "no cook",
    "raw",
    "blender",
    "chilled",
    "refrigerate until",
)
_STOVETOP_KEYWORDS = (
    "skillet",
    "saute",
    "sauté",
    "simmer",
    "stovetop",
    "slow cooker",
    "instant pot",
    "pan-fry",
    "boil",
)


def score_oven_use(instructions: str) -> float:
    """Classify a recipe's indoor cooking heat from its instructions text.

    1.0 = oven-heavy (heats the house), 0.5 = stovetop, 0.0 = grill / no-cook.
    """
    text = (instructions or "").lower()
    if any(kw in text for kw in _OVEN_KEYWORDS):
        return 1.0
    if any(kw in text for kw in _NO_OVEN_KEYWORDS):
        return 0.0
    if any(kw in text for kw in _STOVETOP_KEYWORDS):
        return 0.5
    return 0.5


def _build_prompt(title: str, ingredients: list[str]) -> str:
    """Build the seasonal-scoring prompt from a recipe's title + ingredients."""
    ingredient_lines = "\n".join(f"- {item}" for item in ingredients)
    return (
        "You rate how well a recipe fits each season in the Northern Hemisphere.\n"
        "Consider its ingredients' peak seasons and whether the dish feels light/cooling "
        "(summer) or warm/hearty (winter).\n"
        "Respond with ONLY a JSON object of four numbers from 0.0 to 1.0, keys exactly "
        '"spring", "summer", "fall", "winter".\n\n'
        f"Title: {title}\n"
        f"Ingredients:\n{ingredient_lines}\n"
    )


def _ollama_generate(prompt: str) -> str | None:
    """POST a prompt to Ollama and return the raw response string, or None on failure."""
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
            logger.warning("Ollama response body was not a JSON object")
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


def score_seasons(title: str, ingredients: list[str]) -> dict[str, float] | None:
    """Ask the local LLM to rate a recipe's per-season fit. None on failure.

    Retries once on any failure (network, malformed JSON, validation).
    """
    prompt = _build_prompt(title, ingredients)
    for attempt in range(2):
        parsed = _parse_seasons(_ollama_generate(prompt))
        if parsed is not None:
            return parsed
        logger.info(f"Seasonal scoring attempt {attempt + 1} failed for: {title}")
    return None


def ensure_recipe_tagged(recipe: dict[str, Any]) -> bool:
    """Add missing oven_use / seasonality tags to a recipe in place.

    oven_use is always derivable (rules). seasonality is added only if the LLM
    returns a valid score; on failure it is left absent for a later attempt.
    Returns True if the recipe dict was modified.
    """
    changed = False

    if "oven_use" not in recipe:
        recipe["oven_use"] = score_oven_use(recipe.get("instructions", ""))
        changed = True

    if "seasonality" not in recipe:
        scores = score_seasons(
            recipe.get("title", ""),
            recipe.get("ingredients", []),
        )
        if scores is not None:
            recipe["seasonality"] = scores
            changed = True

    return changed
