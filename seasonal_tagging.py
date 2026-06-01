"""Produce cached seasonal + oven-use tags for recipes.

oven_use is rule-based (deterministic keyword scan). seasonality is produced by
a small local numpy "student" model (see seasonal_model.predict_for_recipe);
there is no network or Ollama dependency at runtime. Scoring never raises:
callers get a neutral 0.5 fallback / unchanged recipes rather than exceptions.
"""

from __future__ import annotations

import logging
from typing import Any

from config import SEASONAL_MODEL_FILENAME
from seasonal_model import predict_for_recipe

logger = logging.getLogger(__name__)

__all__ = [
    "score_oven_use",
    "score_seasons",
    "ensure_recipe_tagged",
]

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


def score_seasons(recipe: dict[str, Any]) -> dict[str, float]:
    """Score a recipe's per-season fit using the local numpy student model.

    Never raises; returns a neutral 0.5 fallback if the model is missing or the
    recipe has no usable text.
    """
    return predict_for_recipe(recipe, SEASONAL_MODEL_FILENAME)


def ensure_recipe_tagged(recipe: dict[str, Any]) -> bool:
    """Add missing oven_use / seasonality tags to a recipe in place.

    oven_use is derived from rules; seasonality comes from the local numpy
    student model. Returns True if the recipe dict was modified.
    """
    changed = False

    if "oven_use" not in recipe:
        recipe["oven_use"] = score_oven_use(recipe.get("instructions", ""))
        changed = True

    if "seasonality" not in recipe:
        recipe["seasonality"] = score_seasons(recipe)
        changed = True

    return changed
