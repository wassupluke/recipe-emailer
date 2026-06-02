"""Config constants for the distilled seasonality model."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config


def test_seasonal_model_filename_default() -> None:
    """SEASONAL_MODEL_FILENAME points at the committed artifact."""
    assert config.SEASONAL_MODEL_FILENAME == "seasonal_model.json"


def test_seasonal_labels_filename_default() -> None:
    """SEASONAL_LABELS_FILENAME points at the teacher label file."""
    assert config.SEASONAL_LABELS_FILENAME == "seasonal_labels.json"


def test_seasonal_constants_exported() -> None:
    """New seasonal-model constants are part of the public config API."""
    assert "SEASONAL_MODEL_FILENAME" in config.__all__
    assert "SEASONAL_LABELS_FILENAME" in config.__all__
