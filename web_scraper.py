"""Web scraping utilities for fetching and parsing recipes."""

import re
import requests
from recipe_scrapers import scrape_html

from config import (
    HEADERS,
    DEBUG_TIMEOUT,
    NORMAL_TIMEOUT,
    REQUIRED_RECIPE_KEYS,
    URL_EXCLUSION_PATTERNS,
    URL_FIX_PREFIX,
    URL_FIX_DOMAIN,
)


def get_html(website: str, debug_mode: bool = False) -> str:
    """Fetch HTML content from a website."""
    timeout = DEBUG_TIMEOUT if debug_mode else NORMAL_TIMEOUT
    
    try:
        with requests.get(website, headers=HEADERS, timeout=timeout) as response:
            return response.text
    except requests.exceptions.Timeout:
        # Handle timeout gracefully
        print(f"{website} timed out. Skipping")
        return ""


def get_recipe_urls(selection: dict, debug_mode: bool = False) -> tuple[list, list]:
    """Get individual recipe URLs from website.

    Returns a tuple with URLs for entrées and side dishes.
    """
    main_html = get_html(selection["main course"], debug_mode)
    side_html = get_html(selection["side dish"], debug_mode)

    main_urls = re.findall(selection["regex"], main_html)
    side_urls = re.findall(selection["regex"], side_html)

    cleanup_recipe_urls(main_urls)
    cleanup_recipe_urls(side_urls)
    return main_urls, side_urls


def cleanup_recipe_urls(urls: list[str]) -> None:
    """Remove bad URL entries based on exclusion patterns."""
    bad_indices = []

    for n, url in enumerate(urls):
        url_lower = url.lower()

        # Fix bad entries
        if url_lower[:len(URL_FIX_PREFIX)] == URL_FIX_PREFIX.lower():
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