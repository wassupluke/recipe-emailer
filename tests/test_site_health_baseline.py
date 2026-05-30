"""Characterization tests for site_health module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from site_health import (
    STATUS_OK,
    STATUS_REGEX_BROKEN,
    STATUS_UNREACHABLE,
    WINDOW_SIZE,
    HealthReport,
    RunOutcome,
    build_report,
    classify_outcome,
    has_something_to_report,
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


def _window(*statuses):
    """Build a window from a sequence of status strings, dated sequentially."""
    return [
        {
            "date": f"2026-05-{i + 1:02d}",
            "status": s,
            "url_count": 0 if s != STATUS_OK else 5,
        }
        for i, s in enumerate(statuses)
    ]


class TestBuildReport:
    def test_current_regex_broken_goes_to_broken(self):
        health = {"Site A — main course": _window(STATUS_OK, STATUS_REGEX_BROKEN)}

        report = build_report(health)

        assert len(report.broken) == 1
        assert report.broken[0].key == "Site A — main course"
        assert report.broken[0].status == STATUS_REGEX_BROKEN
        assert report.unreachable == []
        assert report.flaky == []

    def test_current_unreachable_goes_to_unreachable(self):
        health = {"Site B — side dish": _window(STATUS_OK, STATUS_UNREACHABLE)}

        report = build_report(health)

        assert len(report.unreachable) == 1
        assert report.unreachable[0].key == "Site B — side dish"

    def test_ok_now_but_flaky_goes_to_flaky(self):
        # Ends OK, but 3 failures within the window -> flaky watch
        health = {
            "Site C — main course": _window(
                STATUS_UNREACHABLE, STATUS_REGEX_BROKEN, STATUS_UNREACHABLE, STATUS_OK
            )
        }

        report = build_report(health)

        assert report.broken == []
        assert report.unreachable == []
        assert len(report.flaky) == 1
        assert report.flaky[0].failures == 3

    def test_healthy_site_appears_nowhere(self):
        health = {"Site D — main course": _window(STATUS_OK, STATUS_OK, STATUS_OK)}

        report = build_report(health)

        assert report.broken == []
        assert report.unreachable == []
        assert report.flaky == []

    def test_last_good_is_never_when_window_has_no_ok(self):
        health = {
            "Site E — main course": _window(STATUS_REGEX_BROKEN, STATUS_REGEX_BROKEN)
        }

        report = build_report(health)

        assert report.broken[0].last_good == f"never (in last {WINDOW_SIZE})"

    def test_last_good_reports_most_recent_ok_date(self):
        health = {"Site F — main course": _window(STATUS_OK, STATUS_REGEX_BROKEN)}

        report = build_report(health)

        assert report.broken[0].last_good == "2026-05-01"

    def test_current_failure_takes_priority_over_flaky(self):
        health = {
            "Site G — main course": _window(
                STATUS_REGEX_BROKEN,
                STATUS_UNREACHABLE,
                STATUS_REGEX_BROKEN,
                STATUS_UNREACHABLE,
            )
        }
        report = build_report(health)
        assert len(report.unreachable) == 1
        assert report.flaky == []


class TestHasSomethingToReport:
    def test_false_for_empty_report(self):
        assert has_something_to_report(HealthReport()) is False

    def test_true_when_broken_present(self):
        health = {"Site A — main course": _window(STATUS_REGEX_BROKEN)}
        assert has_something_to_report(build_report(health)) is True
