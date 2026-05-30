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
    "build_report",  # noqa: F822 – added in a later task
    "has_something_to_report",  # noqa: F822 – added in a later task
    "render_health_email",  # noqa: F822 – added in a later task
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
