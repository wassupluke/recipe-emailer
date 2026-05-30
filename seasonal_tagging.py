"""Produce cached seasonal + oven-use tags for recipes.

oven_use is rule-based (deterministic keyword scan). seasonality is produced by
a small local LLM via Ollama. All LLM/network failure is best-effort: callers
get None / unchanged recipes rather than exceptions.
"""

from __future__ import annotations

import json  # noqa: F401
import logging
from typing import Any  # noqa: F401

import requests  # noqa: F401

from config import OLLAMA_HOST, OLLAMA_TIMEOUT, SEASONAL_MODEL  # noqa: F401

logger = logging.getLogger(__name__)

__all__ = [
    "score_oven_use",
    "score_seasons",  # noqa: F822
    "ensure_recipe_tagged",  # noqa: F822
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
