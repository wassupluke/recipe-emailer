"""Characterization tests for seasonal_selection module (pure date math)."""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
from seasonal_selection import (
    final_score,
    heat_preference,
    season_blend,
    weighted_sample,
)


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


SUMMERY = {
    "seasonality": {"spring": 0.3, "summer": 0.9, "fall": 0.3, "winter": 0.1},
    "oven_use": 0.0,  # grilled / no-cook
}
WINTERY = {
    "seasonality": {"spring": 0.2, "summer": 0.1, "fall": 0.4, "winter": 0.9},
    "oven_use": 1.0,  # oven-heavy
}


class TestFinalScore:
    def test_summery_dish_beats_wintery_in_summer(self):
        d = date(2026, 6, 21)
        assert final_score(SUMMERY, d) > final_score(WINTERY, d)

    def test_wintery_dish_beats_summery_in_winter(self):
        d = date(2026, 12, 21)
        assert final_score(WINTERY, d) > final_score(SUMMERY, d)

    def test_untagged_recipe_uses_neutral_and_is_positive(self):
        score = final_score({}, date(2026, 6, 21))
        # fit 0.5 + HEAT_WEIGHT * heat_pref * 0.5 ; stays positive
        assert score > 0.0

    def test_score_never_below_min(self):
        # An oven-heavy, summer-hostile dish at peak summer still floors positive
        hostile = {
            "seasonality": {"spring": 0.0, "summer": 0.0, "fall": 0.0, "winter": 0.0},
            "oven_use": 1.0,
        }
        assert final_score(hostile, date(2026, 6, 21)) >= 0.01


class TestWeightedSample:
    def test_returns_k_distinct_items(self):
        items = ["a", "b", "c", "d"]
        weights = [1.0, 1.0, 1.0, 1.0]
        result = weighted_sample(items, weights, 2)
        assert len(result) == 2
        assert len(set(result)) == 2

    def test_k_larger_than_population_returns_all(self):
        result = weighted_sample(["a", "b"], [1.0, 1.0], 5)
        assert sorted(result) == ["a", "b"]

    def test_all_zero_weights_falls_back_to_uniform(self):
        with patch("seasonal_selection.random.sample", return_value=["b"]) as m:
            result = weighted_sample(["a", "b"], [0.0, 0.0], 1)
        m.assert_called_once()
        assert result == ["b"]

    def test_high_weight_item_picked_with_low_random(self):
        # random.uniform near 0 selects the first positive-weight item
        with patch("seasonal_selection.random.uniform", return_value=0.0):
            result = weighted_sample(["heavy", "light"], [10.0, 0.1], 1)
        assert result == ["heavy"]
