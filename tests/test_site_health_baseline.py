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
    render_health_email,
)


class TestClassifyOutcome:
    """Test classify_outcome status mapping."""

    def test_unreachable_when_not_reachable(self):
        """An unreachable page classifies as UNREACHABLE regardless of url_count."""
        assert classify_outcome(reachable=False, url_count=5) == STATUS_UNREACHABLE

    def test_regex_broken_when_reachable_but_zero_urls(self):
        """A reachable page with zero URLs classifies as REGEX_BROKEN."""
        assert classify_outcome(reachable=True, url_count=0) == STATUS_REGEX_BROKEN

    def test_ok_when_reachable_with_urls(self):
        """A reachable page with URLs classifies as OK."""
        assert classify_outcome(reachable=True, url_count=3) == STATUS_OK


class TestRecordRun:
    """Test record_run window persistence and pruning."""

    def test_appends_outcome_to_new_key(self):
        """Recording a run for a new key creates a single-entry window."""
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
        """Recording a run appends to an existing key's window."""
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
        """The window is pruned to WINDOW_SIZE, dropping the oldest entries."""
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
    """Test build_report categorization of windows."""

    def test_current_regex_broken_goes_to_broken(self):
        """A currently regex-broken site lands in the broken section."""
        health = {"Site A — main course": _window(STATUS_OK, STATUS_REGEX_BROKEN)}

        report = build_report(health)

        assert len(report.broken) == 1
        assert report.broken[0].key == "Site A — main course"
        assert report.broken[0].status == STATUS_REGEX_BROKEN
        assert report.unreachable == []
        assert report.flaky == []

    def test_current_unreachable_goes_to_unreachable(self):
        """A currently unreachable site lands in the unreachable section."""
        health = {"Site B — side dish": _window(STATUS_OK, STATUS_UNREACHABLE)}

        report = build_report(health)

        assert len(report.unreachable) == 1
        assert report.unreachable[0].key == "Site B — side dish"

    def test_ok_now_but_flaky_goes_to_flaky(self):
        """A site that is OK now but failed repeatedly lands in flaky watch."""
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
        """A consistently healthy site appears in no report section."""
        health = {"Site D — main course": _window(STATUS_OK, STATUS_OK, STATUS_OK)}

        report = build_report(health)

        assert report.broken == []
        assert report.unreachable == []
        assert report.flaky == []

    def test_last_good_is_never_when_window_has_no_ok(self):
        """last_good reads 'never' when the window contains no OK run."""
        health = {
            "Site E — main course": _window(STATUS_REGEX_BROKEN, STATUS_REGEX_BROKEN)
        }

        report = build_report(health)

        assert report.broken[0].last_good == f"never (in last {WINDOW_SIZE})"

    def test_last_good_reports_most_recent_ok_date(self):
        """last_good reports the date of the most recent OK run."""
        health = {"Site F — main course": _window(STATUS_OK, STATUS_REGEX_BROKEN)}

        report = build_report(health)

        assert report.broken[0].last_good == "2026-05-01"

    def test_current_failure_takes_priority_over_flaky(self):
        """A current failure is reported as failing rather than merely flaky."""
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
    """Test has_something_to_report truthiness."""

    def test_false_for_empty_report(self):
        """An empty report has nothing to report."""
        assert has_something_to_report(HealthReport()) is False

    def test_true_when_broken_present(self):
        """A report with a broken entry has something to report."""
        health = {"Site A — main course": _window(STATUS_REGEX_BROKEN)}
        assert has_something_to_report(build_report(health)) is True


class TestRenderHealthEmail:
    """Test render_health_email HTML output."""

    def test_includes_broken_section_and_key(self):
        """The rendered email includes the broken section and the affected key."""
        health = {"Site A — main course": _window(STATUS_REGEX_BROKEN)}

        body = render_health_email(build_report(health))

        assert "Likely broken regex" in body
        assert "Site A — main course" in body
        assert body.strip().startswith("<html>")

    def test_omits_empty_sections(self):
        """Sections with no entries are omitted from the rendered email."""
        health = {"Site A — main course": _window(STATUS_REGEX_BROKEN)}

        body = render_health_email(build_report(health))

        assert "Unreachable" not in body
        assert "Flaky watch" not in body

    def test_renders_all_three_sections_when_present(self):
        """All three sections render when broken, unreachable, and flaky exist."""
        health = {
            "Site A — main course": _window(STATUS_REGEX_BROKEN),
            "Site B — side dish": _window(STATUS_UNREACHABLE),
            "Site C — main course": _window(
                STATUS_UNREACHABLE, STATUS_REGEX_BROKEN, STATUS_UNREACHABLE, STATUS_OK
            ),
        }

        body = render_health_email(build_report(health))

        assert "Likely broken regex" in body
        assert "Unreachable" in body
        assert "Flaky watch" in body
