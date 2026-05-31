"""Recipe processing and data fetching logic."""

from tqdm import tqdm

from config import (
    FAILED_FILENAME,
    SCRAPE_FLUSH_INTERVAL,
    UNUSED_MAINS_FILENAME,
    UNUSED_SIDES_FILENAME,
)
from file_utils import save_json
from web_scraper import get_html, get_recipe_urls, scraper


def _flush_scrape_progress(
    target_filename: str,
    target_recipes: dict[str, dict],
    failed_recipes: dict[str, str],
    debug_mode: bool,
) -> None:
    """Persist the active stream's recipes + the failed-recipes skip-list.

    No-op in debug mode (debug must never write the database files).
    """
    if debug_mode:
        return
    save_json(target_filename, target_recipes)
    save_json(FAILED_FILENAME, failed_recipes)


def _scrape_urls_streaming(
    urls: list[str],
    target_recipes: dict[str, dict],
    target_filename: str,
    failed_recipes: dict[str, str],
    debug_mode: bool,
    flush_interval: int = SCRAPE_FLUSH_INTERVAL,
) -> None:
    """Fetch + scrape one page at a time, routing results and flushing periodically.

    Never holds more than one page's HTML in memory. Mutates target_recipes and
    failed_recipes in place. Flushes to disk every `flush_interval` processed URLs
    (and once at the end), except in debug mode.
    """
    for processed, url in enumerate(tqdm(urls), start=1):
        try:
            html = get_html(url, debug_mode)
            recipe = scraper(html, url, failed_recipes)
            del html  # free immediately — peak memory is one page, not all pages
            if recipe is not None:
                target_recipes[url] = recipe
        # Unattended on the Pi: one bad URL (e.g. a network error escaping
        # get_html) must not abort the whole stream or lose flushed progress.
        except Exception as exc:
            print(f"Error scraping {url}: {exc}. Skipping.")
            failed_recipes[url] = f"FAILS due to: {exc}"
        if processed % flush_interval == 0:
            _flush_scrape_progress(
                target_filename, target_recipes, failed_recipes, debug_mode
            )
    _flush_scrape_progress(target_filename, target_recipes, failed_recipes, debug_mode)


def fetch_fresh_recipes(
    websites: dict[str, dict[str, str]],
    unused_main_recipes: dict,
    unused_side_recipes: dict,
    used_recipes: dict,
    failed_recipes: dict,
    debug_mode: bool = False,
) -> tuple[dict[str, dict], dict[str, dict]]:
    """GET LATEST URLS FROM HTML, separating entrées and sides."""
    main_urls, side_urls = [], []
    print("Getting website HTML")
    for site_info in tqdm(websites.values()):
        fresh_main_urls, fresh_side_urls = get_recipe_urls(site_info, debug_mode)
        main_urls.extend(fresh_main_urls)
        side_urls.extend(fresh_side_urls)

    # REMOVE DUPLICATES
    print("Removing duplicate URLs")
    main_urls = list(set(main_urls))
    side_urls = list(set(side_urls))

    # REMOVE URLS ALREADY SCRAPED
    print("Removing URLs already scraped")
    main_urls = [url for url in main_urls if url not in unused_main_recipes]
    side_urls = [url for url in side_urls if url not in unused_side_recipes]

    # REMOVE URLS ALREADY SENT
    print("Removing URLs already sent")
    main_urls = [url for url in main_urls if url not in used_recipes]
    side_urls = [url for url in side_urls if url not in used_recipes]

    # REMOVE URLS THAT FAIL
    print("Removing URLs known to fail")
    main_urls = [url for url in main_urls if url not in failed_recipes]
    side_urls = [url for url in side_urls if url not in failed_recipes]
    print(f"main {len(main_urls)} new\nside {len(side_urls)} new")

    # STREAM: fetch + scrape one page at a time, flushing progress to disk.
    print(f"Scraping {len(main_urls)} main dish recipe pages")
    _scrape_urls_streaming(
        main_urls,
        unused_main_recipes,
        UNUSED_MAINS_FILENAME,
        failed_recipes,
        debug_mode,
    )
    print(f"Scraping {len(side_urls)} side dish recipe pages")
    _scrape_urls_streaming(
        side_urls,
        unused_side_recipes,
        UNUSED_SIDES_FILENAME,
        failed_recipes,
        debug_mode,
    )
    print(
        f"main {len(unused_main_recipes)} new total, "
        f"side {len(unused_side_recipes)} new total"
    )

    return unused_main_recipes, unused_side_recipes
