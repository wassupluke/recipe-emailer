"""Characterization tests for site_health module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from site_health import (
    STATUS_OK,
    STATUS_REGEX_BROKEN,
    STATUS_UNREACHABLE,
    WINDOW_SIZE,
    RunOutcome,
    classify_outcome,
    record_run,
)


class TestClassifyOutcome:
    def test_unreachable_when_not_reachable(self):
        assert classify_outcome(reachable=False, url_count=5) == STATUS_UNREACHABLE

    def test_regex_broken_when_reachable_but_zero_urls(self):
        assert classify_outcome(reachable=True, url_count=0) == STATUS_REGEX_BROKEN

    def test_ok_when_reachable_with_urls(self):
        assert classify_outcome(reachable=True, url_count=3) == STATUS_OK


class TestRecordRun:
    def test_appends_outcome_to_new_key(self):
        health: dict = {}
        outcomes = [
            RunOutcome(key="Site A — main course", status=STATUS_OK, url_count=4)
        ]

        record_run(health, outcomes, "2026-05-29")

        assert health == {
            "Site A — main course": [
                {"date": "2026-05-29", "status": STATUS_OK, "url_count": 4}
            ]
        }

    def test_appends_to_existing_window(self):
        health = {
            "Site A — main course": [
                {"date": "2026-05-22", "status": STATUS_OK, "url_count": 4}
            ]
        }
        outcomes = [
            RunOutcome(
                key="Site A — main course", status=STATUS_REGEX_BROKEN, url_count=0
            )
        ]

        record_run(health, outcomes, "2026-05-29")

        window = health["Site A — main course"]
        assert len(window) == 2
        assert window[-1]["status"] == STATUS_REGEX_BROKEN

    def test_prunes_to_window_size(self):
        health: dict = {}
        for day in range(1, WINDOW_SIZE + 2):  # one more than the window holds
            record_run(
                health,
                [RunOutcome(key="Site A — main course", status=STATUS_OK, url_count=1)],
                f"2026-05-{day:02d}",
            )

        window = health["Site A — main course"]
        assert len(window) == WINDOW_SIZE
        # Oldest (day 1) was pruned; newest (day WINDOW_SIZE+1) retained
        assert window[0]["date"] == "2026-05-02"
        assert window[-1]["date"] == f"2026-05-{WINDOW_SIZE + 1:02d}"
