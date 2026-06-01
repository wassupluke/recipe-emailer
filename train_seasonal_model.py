#!/usr/bin/env python3
"""Desktop training: distill teacher labels into a TF-IDF + ridge student.

Reads seasonal_labels.json + the recipe corpus, fits TF-IDF + multi-output ridge,
exports the dependency-free seasonal_model.json (numpy-only inference on the Pi),
and reports holdout MAE vs a deterministic produce-calendar baseline.

    python train_seasonal_model.py
"""

from __future__ import annotations

import json
import logging
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split

from config import (
    SEASONAL_LABELS_FILENAME,
    SEASONAL_MODEL_FILENAME,
    UNUSED_MAINS_FILENAME,
    UNUSED_SIDES_FILENAME,
)
from file_utils import load_json
from seasonal_model import SEASONS, predict_seasons, recipe_text, tokenize

logger = logging.getLogger(__name__)

# Minimal seasonal-produce calendar for the "do we even need ML" baseline.
_PRODUCE = {
    "spring": ("asparagus", "pea", "peas", "radish", "rhubarb", "artichoke", "spring"),
    "summer": ("tomato", "corn", "zucchini", "basil", "berry", "peach", "cucumber"),
    "fall": ("squash", "pumpkin", "apple", "sweet potato", "kale", "brussels"),
    "winter": ("root", "braise", "stew", "citrus", "cabbage", "parsnip", "turnip"),
}


def fit(
    texts: list[str], Y: np.ndarray, alpha: float = 1.0, max_features: int = 4000
) -> tuple[TfidfVectorizer, Ridge]:
    """Fit TF-IDF (l2) + multi-output ridge on texts -> 4 season targets."""
    vec = TfidfVectorizer(
        tokenizer=tokenize,
        token_pattern=None,
        lowercase=False,  # tokenize() already lowercases
        max_features=max_features,
        norm="l2",
        smooth_idf=True,
        sublinear_tf=False,
    )
    X = vec.fit_transform(texts)
    ridge = Ridge(alpha=alpha)
    ridge.fit(X, Y)
    return vec, ridge


def export_model(vec: TfidfVectorizer, ridge: Ridge) -> dict[str, Any]:
    """Serialize the fitted vectorizer + ridge into the numpy-only artifact dict."""
    return {
        "version": 1,
        "seasons": list(SEASONS),
        "vocabulary": {t: int(i) for t, i in vec.vocabulary_.items()},
        "idf": vec.idf_.tolist(),
        "coef": ridge.coef_.tolist(),
        "intercept": ridge.intercept_.tolist(),
    }


def calendar_baseline(text: str) -> dict[str, float]:
    """Deterministic baseline: per-season share of matched produce keywords."""
    low = text.lower()
    raw = {
        season: float(sum(1 for kw in kws if kw in low))
        for season, kws in _PRODUCE.items()
    }
    total = sum(raw.values())
    if total == 0:
        return dict.fromkeys(SEASONS, 0.5)
    return {s: raw[s] / total for s in SEASONS}


def _load_dataset() -> tuple[list[str], np.ndarray]:
    """Join labels with recipe text; return aligned (texts, Y)."""
    labels, _ = load_json(SEASONAL_LABELS_FILENAME)
    mains, _ = load_json(UNUSED_MAINS_FILENAME)
    sides, _ = load_json(UNUSED_SIDES_FILENAME)
    corpus = {**mains, **sides}
    texts: list[str] = []
    rows: list[list[float]] = []
    for url, label in labels.items():
        if url in corpus:
            texts.append(recipe_text(corpus[url]))
            rows.append([label[s] for s in SEASONS])
    return texts, np.array(rows)


def main() -> None:
    """Train, evaluate vs baseline, and write SEASONAL_MODEL_FILENAME."""
    logging.basicConfig(level=logging.INFO)
    texts, Y = _load_dataset()
    logger.info(f"Training on {len(texts)} labeled recipes")
    tr_x, te_x, tr_y, te_y = train_test_split(texts, Y, test_size=0.15, random_state=0)
    vec, ridge = fit(tr_x, tr_y)
    artifact = export_model(vec, ridge)

    student = np.array(
        [[predict_seasons(t, artifact)[s] for s in SEASONS] for t in te_x]
    )
    baseline = np.array([[calendar_baseline(t)[s] for s in SEASONS] for t in te_x])
    logger.info(f"Student  MAE: {np.mean(np.abs(student - te_y)):.3f}")
    logger.info(f"Calendar MAE: {np.mean(np.abs(baseline - te_y)):.3f}")

    with open(SEASONAL_MODEL_FILENAME, "w", encoding="utf-8") as f:
        json.dump(artifact, f)
    logger.info(f"Wrote {SEASONAL_MODEL_FILENAME} (vocab={len(artifact['idf'])})")


if __name__ == "__main__":
    main()
