"""Pure-numpy distilled seasonality student model (Pi-side inference).

Loads the TF-IDF + ridge artifact produced by train_seasonal_model.py and scores
a recipe's per-season fit using only numpy (no scikit-learn, no Ollama). The
tokenizer and text-blob builder here are imported by the training script so that
train-time and inference-time featurization are byte-for-byte identical.
"""

from __future__ import annotations

import re
from typing import Any

_TOKEN_RE = re.compile(r"\b\w\w+\b", re.UNICODE)

SEASONS = ("spring", "summer", "fall", "winter")


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
