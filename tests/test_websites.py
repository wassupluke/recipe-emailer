"""Structural validation for the WEBSITES scrape config.

These guard against malformed entries when sites are added/edited: every site
must have a compilable regex with exactly one capture group (the recipe URL the
scraper extracts via ``re.findall``) and reachable-looking main/side index URLs.
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from websites import WEBSITES

_REQUIRED_KEYS = ("regex", "main course", "side dish")
_SITE_IDS = list(WEBSITES)


def test_websites_is_nonempty() -> None:
    """There is at least one configured site."""
    assert len(WEBSITES) > 0


@pytest.mark.parametrize("name", _SITE_IDS)
class TestWebsiteEntry:
    """Each WEBSITES entry is structurally valid."""

    def test_has_required_keys(self, name: str) -> None:
        """Entry has regex + main course + side dish keys, all non-empty str."""
        entry = WEBSITES[name]
        for key in _REQUIRED_KEYS:
            assert key in entry, f"{name} missing '{key}'"
            assert (
                isinstance(entry[key], str) and entry[key].strip()
            ), f"{name}['{key}'] must be a non-empty string"

    def test_regex_compiles(self, name: str) -> None:
        """The site's regex is a valid pattern."""
        try:
            re.compile(WEBSITES[name]["regex"])
        except re.error as e:
            pytest.fail(f"{name} regex does not compile: {e}")

    def test_regex_has_exactly_one_capture_group(self, name: str) -> None:
        """re.findall yields the URL string, so exactly one capturing group."""
        groups = re.compile(WEBSITES[name]["regex"]).groups
        assert groups == 1, f"{name} regex has {groups} capture groups, expected 1"

    def test_index_urls_are_http(self, name: str) -> None:
        """Main and side index URLs are absolute http(s) URLs."""
        for key in ("main course", "side dish"):
            url = WEBSITES[name][key]
            assert url.startswith(
                ("http://", "https://")
            ), f"{name}['{key}'] is not an absolute URL: {url!r}"


def test_site_names_are_unique() -> None:
    """Dict keys are inherently unique; guard against accidental value aliasing."""
    main_urls = [v["main course"] for v in WEBSITES.values()]
    assert len(main_urls) == len(set(main_urls)), "duplicate main-course index URLs"
