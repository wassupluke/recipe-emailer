"""Web scraping utilities for fetching and parsing recipes."""

import re
from dataclasses import dataclass

import requests
from recipe_scrapers import scrape_html

from config import (
    DEBUG_TIMEOUT,
    HEADERS,
    NORMAL_TIMEOUT,
    REQUIRED_RECIPE_KEYS,
    URL_EXCLUSION_PATTERNS,
    URL_FIX_DOMAIN,
    URL_FIX_PREFIX,
)
from site_health import classify_outcome


@dataclass(frozen=True)
class PageResult:
    """Outcome of fetching a listing page, for health monitoring.

    reachable is True only for an HTTP 200 with a non-empty body.
    """

    reachable: bool
    status_code: int | None
    html: str


def _decode(response: requests.Response) -> str:
    """Decode a response body, sniffing the charset when the server omits one.

    requests falls back to ISO-8859-1 for text/* responses with no charset in
    the Content-Type header, which corrupts UTF-8 pages (en-dashes and curly
    quotes render as mojibake like "5â€"6"). Trust a declared charset; otherwise
    sniff the actual bytes.
    """
    if "charset" not in response.headers.get("content-type", "").lower():
        response.encoding = response.apparent_encoding
    return response.text


def fetch_page(url: str, debug_mode: bool = False) -> PageResult:
    """Fetch a listing page, reporting reachability for health monitoring."""
    timeout = DEBUG_TIMEOUT if debug_mode else NORMAL_TIMEOUT
    try:
        with requests.get(url, headers=HEADERS, timeout=timeout) as response:
            body = _decode(response)
            reachable = response.status_code == 200 and bool(body.strip())
            return PageResult(
                reachable=reachable,
                status_code=response.status_code,
                html=body,
            )
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        print(f"{url} unreachable. Skipping")
        return PageResult(reachable=False, status_code=None, html="")


def get_html(website: str, debug_mode: bool = False) -> str:
    """Fetch HTML content from a website."""
    timeout = DEBUG_TIMEOUT if debug_mode else NORMAL_TIMEOUT

    try:
        with requests.get(website, headers=HEADERS, timeout=timeout) as response:
            return _decode(response)
    except requests.exceptions.Timeout:
        # Handle timeout gracefully
        print(f"{website} timed out. Skipping")
        return ""


def get_recipe_urls(
    selection: dict, debug_mode: bool = False
) -> tuple[list[str], list[str], dict[str, tuple[str, int]]]:
    """Get individual recipe URLs from a website's listing pages.

    Returns (main_urls, side_urls, statuses) where statuses maps each course
    ("main course" / "side dish") to (status, raw_match_count) for health
    monitoring. Status is derived from the raw regex match count, before
    cleanup_recipe_urls filters excluded URLs, so an all-filtered page is not
    mistaken for a broken regex.
    """
    url_lists: dict[str, list[str]] = {}
    statuses: dict[str, tuple[str, int]] = {}

    for course in ("main course", "side dish"):
        page = fetch_page(selection[course], debug_mode)
        urls = re.findall(selection["regex"], page.html)
        match_count = len(urls)
        cleanup_recipe_urls(urls)
        statuses[course] = (classify_outcome(page.reachable, match_count), match_count)
        url_lists[course] = urls

    return url_lists["main course"], url_lists["side dish"], statuses


def cleanup_recipe_urls(urls: list[str]) -> None:
    """Remove bad URL entries based on exclusion patterns."""
    bad_indices = []

    for n, url in enumerate(urls):
        url_lower = url.lower()

        # Fix bad entries
        if url_lower[: len(URL_FIX_PREFIX)] == URL_FIX_PREFIX.lower():
            urls[n] = f"{URL_FIX_DOMAIN}{url}"
            url_lower = urls[n].lower()  # Update for pattern checking

        # Check against exclusion patterns
        should_exclude = False
        for pattern in URL_EXCLUSION_PATTERNS:
            # Check if all keywords in the pattern are present in the URL
            if all(keyword in url_lower for keyword in pattern):
                should_exclude = True
                break

        if should_exclude:
            bad_indices.append(n)

    # Remove bad entries in reverse order to avoid index shifting
    for i in reversed(bad_indices):
        del urls[i]


def scraper(html: str, url: str, failed_recipes: dict) -> dict | None:
    """Scrape URL and returns hhursev recipe_scraper elements."""
    try:
        scrape = scrape_html(html, url)
        recipe_elements = scrape.to_json()
        # Replace returned canonical_url with the input URL if they differ
        if recipe_elements["canonical_url"] != url:
            recipe_elements["canonical_url"] = url
        # Verify recipe_elements are valid before returning
        for key in REQUIRED_RECIPE_KEYS:
            if key not in [element.lower() for element in recipe_elements]:
                raise ValueError(
                    f"Didn't find {key} in list of recipe elements. Failing. "
                    f"{recipe_elements['canonical_url']}"
                )

            elif not recipe_elements["ingredients"]:
                raise ValueError("Ingredients list empty")

            elif recipe_elements["instructions"] == "":
                raise ValueError("Instructions blank")

            elif recipe_elements["image"] is None:
                raise ValueError("No recipe image")

    except ValueError as e:
        failed_recipes[url] = f"FAILS due to: {e}"
        return None

    # I run this as an unattended script, so handle other errors and keep going
    except Exception as e:
        failed_recipes[url] = f"FAILS due to: {e}"
        return None

    # Everything passed, return the elements
    return recipe_elements
