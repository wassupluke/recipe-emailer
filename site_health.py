"""Site-health monitoring: track per-site URL-extraction outcomes over time.

Records, for each (website, course) listing page, whether the scrape regex
matched URLs, the page was unreachable, or all is well — and surfaces trends
so the maintainer learns when a site's regex needs fixing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

__all__ = [
    "STATUS_OK",
    "STATUS_REGEX_BROKEN",
    "STATUS_UNREACHABLE",
    "WINDOW_SIZE",
    "FLAKY_THRESHOLD",
    "RunOutcome",
    "ReportEntry",
    "HealthReport",
    "classify_outcome",
    "record_run",
    "build_report",
    "has_something_to_report",
    "render_health_email",
]

# Status constants
STATUS_OK = "OK"
STATUS_REGEX_BROKEN = "REGEX_BROKEN"
STATUS_UNREACHABLE = "UNREACHABLE"

# Rolling-window + flakiness tuning
WINDOW_SIZE = 8
FLAKY_THRESHOLD = 3

_FAILURE_STATUSES = (STATUS_REGEX_BROKEN, STATUS_UNREACHABLE)


@dataclass(frozen=True)
class RunOutcome:
    """One (site, course) outcome for the current run."""

    key: str  # "<Site Name> — <course>"
    status: str  # one of the STATUS_* constants
    url_count: int


@dataclass(frozen=True)
class ReportEntry:
    """A single line in the health report."""

    key: str
    status: str
    last_good: str  # YYYY-MM-DD or "never (in last N)"
    failures: int  # failures within the window
    window: int  # number of runs the window currently holds


@dataclass
class HealthReport:
    """Computed health report split into three sections."""

    broken: list[ReportEntry] = field(default_factory=list)
    unreachable: list[ReportEntry] = field(default_factory=list)
    flaky: list[ReportEntry] = field(default_factory=list)


def classify_outcome(reachable: bool, url_count: int) -> str:
    """Classify a single index-page fetch into a status constant."""
    if not reachable:
        return STATUS_UNREACHABLE
    if url_count == 0:
        return STATUS_REGEX_BROKEN
    return STATUS_OK


def record_run(
    health_data: dict[str, list[dict[str, Any]]],
    outcomes: list[RunOutcome],
    run_date: str,
) -> dict[str, list[dict[str, Any]]]:
    """Append each outcome to its key's window and prune to WINDOW_SIZE.

    Mutates and returns health_data.
    """
    for outcome in outcomes:
        window = health_data.setdefault(outcome.key, [])
        window.append(
            {
                "date": run_date,
                "status": outcome.status,
                "url_count": outcome.url_count,
            }
        )
        if len(window) > WINDOW_SIZE:
            del window[: len(window) - WINDOW_SIZE]
    return health_data


def _last_good(window: list[dict[str, Any]]) -> str:
    """Return the date of the most recent OK entry, or a 'never' sentinel."""
    for entry in reversed(window):
        if entry["status"] == STATUS_OK:
            return str(entry["date"])
    return f"never (in last {WINDOW_SIZE})"


def _count_failures(window: list[dict[str, Any]]) -> int:
    """Count non-OK entries within the window."""
    return sum(1 for e in window if e["status"] in _FAILURE_STATUSES)


def build_report(health_data: dict[str, list[dict[str, Any]]]) -> HealthReport:
    """Compute broken / unreachable / flaky sections from the windows.

    'Current' status is the most recent entry in each key's window. A key whose
    current status is OK still lands on the flaky watch if it failed at least
    FLAKY_THRESHOLD times within the window. A current REGEX_BROKEN/UNREACHABLE
    status takes precedence over the flaky watch, so the flaky branch only
    applies when the current status is OK.
    """
    report = HealthReport()

    for key, window in health_data.items():
        if not window:
            continue
        current = window[-1]["status"]
        entry = ReportEntry(
            key=key,
            status=current,
            last_good=_last_good(window),
            failures=_count_failures(window),
            window=len(window),
        )

        if current == STATUS_REGEX_BROKEN:
            report.broken.append(entry)
        elif current == STATUS_UNREACHABLE:
            report.unreachable.append(entry)
        elif entry.failures >= FLAKY_THRESHOLD:
            report.flaky.append(entry)

    return report


def has_something_to_report(report: HealthReport) -> bool:
    """True iff any of the three report sections is populated."""
    return bool(report.broken or report.unreachable or report.flaky)


def _render_section(title: str, entries: list[ReportEntry]) -> str:
    """Render one report section, or '' if it has no entries."""
    if not entries:
        return ""
    rows = "\n".join(
        f"  <li><strong>{e.key}</strong> — current: {e.status}, "
        f"last good: {e.last_good}, failed {e.failures} of last {e.window} runs</li>"
        for e in entries
    )
    return f"<h2>{title}</h2>\n<ul>\n{rows}\n</ul>\n"


def render_health_email(report: HealthReport) -> str:
    """Render the HTML email body for a health report, omitting empty sections."""
    sections = (
        _render_section("🔴 Likely broken regex", report.broken)
        + _render_section("🟡 Unreachable", report.unreachable)
        + _render_section("📉 Flaky watch", report.flaky)
    )
    return (
        "<html>\n<body>\n"
        "<h1>Recipe Emailer — Site Health</h1>\n"
        f"{sections}"
        "</body>\n</html>\n"
    )
