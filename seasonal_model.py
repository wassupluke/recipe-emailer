"""Pure-numpy distilled seasonality student model (Pi-side inference).

Loads the TF-IDF + ridge artifact produced by train_seasonal_model.py and scores
a recipe's per-season fit using only numpy (no scikit-learn, no Ollama). The
tokenizer and text-blob builder here are imported by the training script so that
train-time and inference-time featurization are byte-for-byte identical.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import numpy as np

_TOKEN_RE = re.compile(r"\b\w\w+\b", re.UNICODE)

SEASONS = ("spring", "summer", "fall", "winter")

logger = logging.getLogger(__name__)

_NEUTRAL = 0.5


def tokenize(text: str) -> list[str]:
    """Lowercase + split text into word tokens of length >= 2 (sklearn default)."""
    return _TOKEN_RE.findall(text.lower())


def recipe_text(recipe: dict[str, Any]) -> str:
    """Build the TF-IDF input blob from a recipe's title, ingredients, keywords."""
    parts: list[str] = [str(recipe.get("title", "") or "")]
    parts.extend(str(i) for i in (recipe.get("ingredients") or []))
    keywords = recipe.get("keywords")
    if isinstance(keywords, str):
        parts.append(keywords)
    elif isinstance(keywords, list):
        parts.extend(str(k) for k in keywords)
    return " ".join(p for p in parts if p)


def load_model(path: str) -> dict[str, Any]:
    """Load the exported JSON artifact (vocabulary, idf, coef, intercept)."""
    with open(path, encoding="utf-8") as f:
        return dict(json.load(f))


def _neutral() -> dict[str, float]:
    """Return the neutral fallback score (0.5 for every season)."""
    return dict.fromkeys(SEASONS, _NEUTRAL)


def predict_seasons(text: str, model: dict[str, Any]) -> dict[str, float]:
    """Score a text blob's per-season fit via TF-IDF (l2) + ridge, clamped [0,1]."""
    vocab: dict[str, int] = model["vocabulary"]
    idf = np.asarray(model["idf"], dtype=float)
    vec = np.zeros(len(idf), dtype=float)
    for token in tokenize(text):
        idx = vocab.get(token)
        if idx is not None:
            vec[idx] += 1.0
    vec *= idf
    norm = float(np.linalg.norm(vec))
    if norm > 0.0:
        vec /= norm
    coef = np.asarray(model["coef"], dtype=float)
    intercept = np.asarray(model["intercept"], dtype=float)
    scores = np.clip(coef @ vec + intercept, 0.0, 1.0)
    return {s: float(x) for s, x in zip(model["seasons"], scores, strict=True)}


def predict_for_recipe(recipe: dict[str, Any], model_path: str) -> dict[str, float]:
    """Score a recipe; never raises. Neutral 0.5 fallback on any failure/empty text."""
    try:
        text = recipe_text(recipe)
        if not text.strip():
            return _neutral()
        return predict_seasons(text, load_model(model_path))
    except Exception as e:  # best-effort: must not break the recipe run
        logger.warning(f"Seasonal student prediction failed: {e}")
        return _neutral()
