"""Selection-time seasonal scoring — pure date math, no network.

Turns today's date into per-season blend weights and a continuous winter↔summer
heat preference, then scores already-tagged recipes for the weekly pick.
"""

from __future__ import annotations

import random
from datetime import date  # noqa: TC003
from typing import Any

from config import (
    FALL_CENTER,
    HEAT_WEIGHT,
    MIN_SCORE,
    SPRING_CENTER,
    SUMMER_CENTER,
    WINTER_CENTER,
)

__all__ = [
    "season_blend",
    "season_fit",
    "heat_preference",
    "final_score",
    "weighted_sample",
]

_YEAR_DAYS = 365

# Season centers on the day-of-year ring, ordered.
_SEASON_CENTERS: list[tuple[str, int]] = sorted(
    [
        ("spring", SPRING_CENTER),
        ("summer", SUMMER_CENTER),
        ("fall", FALL_CENTER),
        ("winter", WINTER_CENTER),
    ],
    key=lambda pair: pair[1],
)

# Per-season heat values for heat_preference.
_SEASON_HEAT = {"winter": 1.0, "summer": -1.0, "spring": 0.0, "fall": 0.0}


def _ring_distance(a: int, b: int) -> int:
    """Shortest forward distance from a to b around the day-of-year ring."""
    return (b - a) % _YEAR_DAYS


def season_blend(today: date) -> dict[str, float]:
    """Return blend weights across the four seasons for a date.

    The two season centers bracketing today's day-of-year share all the weight,
    linearly by proximity; the other two seasons are 0.0. Weights sum to 1.0.
    """
    doy = today.timetuple().tm_yday
    weights = {name: 0.0 for name, _ in _SEASON_CENTERS}

    # Find the bracketing pair: the center at-or-before doy, and the next center.
    centers = _SEASON_CENTERS
    n = len(centers)
    for i in range(n):
        name_lo, center_lo = centers[i]
        name_hi, center_hi = centers[(i + 1) % n]
        span = _ring_distance(center_lo, center_hi)
        offset = _ring_distance(center_lo, doy)
        if offset <= span:
            # doy lies in the arc from center_lo to center_hi
            frac = offset / span if span else 0.0
            weights[name_lo] = 1.0 - frac
            weights[name_hi] = frac
            return weights

    # Fallback (should not happen): all weight on nearest center.
    nearest = min(centers, key=lambda pair: _ring_distance(pair[1], doy))
    weights[nearest[0]] = 1.0
    return weights


def heat_preference(today: date) -> float:
    """Continuous winter↔summer preference in [-1, +1] (+1 deep winter)."""
    weights = season_blend(today)
    return sum(weights[name] * _SEASON_HEAT[name] for name in weights)


def season_fit(recipe: dict[str, Any], today: date) -> float:
    """How well a recipe fits the current blended season (0-1). Untagged -> 0.5."""
    seasonality = recipe.get("seasonality")
    if not isinstance(seasonality, dict):
        return 0.5
    weights = season_blend(today)
    return sum(weights[name] * float(seasonality.get(name, 0.0)) for name in weights)


def final_score(recipe: dict[str, Any], today: date) -> float:
    """Combine seasonal fit and oven-use heat preference into a positive weight."""
    fit = season_fit(recipe, today)
    oven = float(recipe.get("oven_use", 0.5))
    score = fit + HEAT_WEIGHT * heat_preference(today) * oven
    return max(score, MIN_SCORE)


def weighted_sample(items: list[Any], weights: list[float], k: int) -> list[Any]:
    """Draw k distinct items without replacement, prob. proportional to weight.

    Falls back to uniform sampling if all weights are non-positive.
    """
    k = min(k, len(items))
    if k <= 0:
        return []
    if sum(w for w in weights if w > 0) <= 0:
        return random.sample(items, k)

    pool = list(zip(items, weights, strict=False))
    chosen: list[Any] = []
    for _ in range(k):
        total = sum(w for _, w in pool)
        r = random.uniform(0, total)
        upto = 0.0
        for idx, (item, w) in enumerate(pool):
            upto += w
            if upto >= r:
                chosen.append(item)
                pool.pop(idx)
                break
        else:
            # Floating-point edge: take the last remaining item.
            chosen.append(pool.pop()[0])
    return chosen
