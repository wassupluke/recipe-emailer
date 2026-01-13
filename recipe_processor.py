"""Recipe processing and data fetching logic."""

from tqdm import tqdm

from web_scraper import get_recipe_urls, get_html, scraper


def get_fresh_data(
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

    # GET HTML FOR EACH RECIPE URL
    main_htmls, side_htmls = {}, {}
    print(f"Getting HTML for {len(main_urls)} main dish recipe pages")
    for url in tqdm(main_urls):
        main_htmls[url] = get_html(url, debug_mode)
    print(f"Getting HTML for {len(side_urls)} side dish recipe pages")
    for url in tqdm(side_urls):
        side_htmls[url] = get_html(url, debug_mode)

    # USE HHURSEV'S RECIPE SCRAPER
    if len(main_htmls) > 0:
        print("Scraping main course HTMLs")
        for url, html in (item for item in tqdm(main_htmls.items())):
            recipe_elements = scraper(html, url, failed_recipes)
            if recipe_elements is not None:
                unused_main_recipes[url] = recipe_elements
    if len(side_htmls) > 0:
        print("Scraping side dish HTMLs")
        for url, html in (item for item in tqdm(side_htmls.items())):
            recipe_elements = scraper(html, url, failed_recipes)
            if recipe_elements is not None:
                unused_side_recipes[url] = recipe_elements
    print(f"main {len(unused_main_recipes)} {unused_main_recipes=}")
    print(f"side {len(unused_side_recipes)} {unused_side_recipes=}")

    return unused_main_recipes, unused_side_recipes