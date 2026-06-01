"""Tests for the desktop training/export script."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
import seasonal_model
import train_seasonal_model


def test_export_roundtrip_matches_sklearn(tmp_path: Path) -> None:
    """The exported numpy artifact reproduces sklearn predictions within tol."""
    texts = [
        "tomato basil corn zucchini",
        "butternut squash root vegetable braise",
        "asparagus pea spring greens",
        "apple pumpkin squash cinnamon",
    ]
    Y = np.array(
        [
            [0.2, 0.9, 0.1, 0.0],
            [0.0, 0.0, 0.6, 0.9],
            [0.9, 0.2, 0.0, 0.0],
            [0.1, 0.0, 0.9, 0.6],
        ]
    )
    vec, ridge = train_seasonal_model.fit(texts, Y, alpha=1.0, max_features=50)
    artifact = train_seasonal_model.export_model(vec, ridge)
    sk_pred = np.clip(ridge.predict(vec.transform([texts[0]]))[0], 0.0, 1.0)
    np_pred = seasonal_model.predict_seasons(texts[0], artifact)
    np_vec = np.array([np_pred[s] for s in seasonal_model.SEASONS])
    assert np.allclose(np_vec, sk_pred, atol=1e-9)


def test_calendar_baseline_runs() -> None:
    """The deterministic produce-calendar baseline returns 4 scores in [0,1]."""
    scores = train_seasonal_model.calendar_baseline("fresh tomato and corn salad")
    assert set(scores) == set(seasonal_model.SEASONS)
    assert all(0.0 <= v <= 1.0 for v in scores.values())
