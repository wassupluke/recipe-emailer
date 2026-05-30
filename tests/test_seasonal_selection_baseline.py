"""Characterization tests for seasonal_selection module (pure date math)."""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from seasonal_selection import heat_preference, season_blend


def _doy(year: int, month: int, day: int) -> date:
    return date(year, month, day)


class TestSeasonBlend:
    def test_weights_sum_to_one(self):
        weights = season_blend(_doy(2026, 8, 1))
        assert abs(sum(weights.values()) - 1.0) < 1e-9

    def test_summer_center_is_almost_all_summer(self):
        weights = season_blend(_doy(2026, 6, 21))  # ~SUMMER_CENTER
        assert weights["summer"] > 0.95
        assert weights["spring"] < 0.05
        assert weights["fall"] == 0.0
        assert weights["winter"] == 0.0

    def test_winter_center_is_almost_all_winter(self):
        weights = season_blend(_doy(2026, 12, 21))  # ~WINTER_CENTER
        assert weights["winter"] > 0.95

    def test_shoulder_date_splits_two_seasons(self):
        # Early November sits between fall (Sep 22) and winter (Dec 21)
        weights = season_blend(_doy(2026, 11, 5))
        assert weights["fall"] > 0.0
        assert weights["winter"] > 0.0
        assert weights["spring"] == 0.0
        assert weights["summer"] == 0.0
        assert abs(weights["fall"] + weights["winter"] - 1.0) < 1e-9

    def test_year_wrap_early_january_splits_winter_and_spring(self):
        # Early January is past winter center (Dec 21), heading to spring
        weights = season_blend(_doy(2026, 1, 5))
        assert weights["winter"] > 0.0
        assert weights["spring"] > 0.0
        assert weights["summer"] == 0.0
        assert weights["fall"] == 0.0


class TestHeatPreference:
    def test_winter_center_near_plus_one(self):
        assert heat_preference(_doy(2026, 12, 21)) > 0.9

    def test_summer_center_near_minus_one(self):
        assert heat_preference(_doy(2026, 6, 21)) < -0.9

    def test_equinoxes_near_zero(self):
        assert abs(heat_preference(_doy(2026, 3, 20))) < 0.1  # spring center
        assert abs(heat_preference(_doy(2026, 9, 22))) < 0.1  # fall center
