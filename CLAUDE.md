# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run (sends to BCC recipients, scrapes ~18 sites, ~150s)
python main.py

# Debug mode: prompts for a single site, sends only to SENDER,
# skips all persistence + website publish
python main.py -d

# Tests
pytest                              # all tests
pytest tests/test_file_utils.py -v  # single file
pytest --cov --cov-report=term-missing

# Quality gate (mirrors CI)
mypy . --strict && ruff check . && black --check .

# Production entry point (used by cron)
./cook.sh   # cd, activate .venv, python3 main.py >> cronjob.log
```

Python ≥3.11. Dev tooling installed via `pip install -e ".[dev]"`.

## Architecture

Flat module layout (no package) — every module is a top-level file importing siblings directly. `main.py` orchestrates a linear pipeline; each stage lives in its own module:

```
scrape (recipe_processor → web_scraper)
  → select proteins (recipe_selector.select_random_proteins)
  → ensure veggies / add sides (recipe_selector.ensure_veggies)
  → render (html_generator.generate_html_email)
  → send (email_sender.send_email)
  → publish to website (website_publisher.publish_meals_page)
  → update tracking JSON (file_utils.save_json)
```

`config.py` centralizes all constants + env vars; nearly every module imports from it. `main.py` passes a single `context` dict between its private `_*` helpers.

### State lives in committed JSON files

The four `*_recipes.json` files in the repo root **are the database** and are tracked in git (see commits like "update DBs"). They are keyed by recipe URL:

- `unused_mains_recipes.json` / `unused_sides_recipes.json` — scraped-but-not-yet-sent recipes
- `used_recipes.json` — `{url: date_sent}`, prevents repeats
- `failed_recipes.json` — `{url: failure_reason}`, URLs to skip

On each run, `unused_mains` is re-scraped only if it's newly created or older than `FILE_AGE_THRESHOLD` (12h). When a recipe is emailed it moves from an `unused_*` file into `used_recipes`. Debug mode never writes these files.

### Two recipe data shapes (easy to confuse)

1. **Raw recipe** — the value stored in the JSON files: a dict from `recipe_scrapers.scrape_html(...).to_json()` with keys `title`, `ingredients`, `instructions`, `image`, `site_name`, `host`, etc. (`REQUIRED_RECIPE_KEYS` in config). A "recipe item" wraps one as `{url: recipe_dict}`.
2. **Meal item** — what `ensure_veggies` produces and what `html_generator`/tracking consume: `{"type": ..., "obj": {url: recipe_dict}}` where `type` is `single_main`, `combo_main`, or `combo_side`. Unwrap the recipe with `info["obj"][next(iter(info["obj"]))]`.

### Selection logic (recipe_selector.py)

Recipes are categorized seafood vs. landfood by substring-matching `SEAFOOD_PROTEINS`/`LANDFOOD_PROTEINS` against ingredient strings. `_select_meal_mix` sends 2 land + 1 seafood when seafood exists, else 3 land, else raises `InsufficientRecipesError`. A main lacking any `VEGGIES` ingredient gets a random side dish appended (producing the `combo_*` pair).

### Scraping (websites.py + web_scraper.py)

`WEBSITES` maps a site name → `{regex, "main course" url, "side dish" url}`. Each site's index pages are fetched and `regex` extracts individual recipe URLs. URLs are filtered through `URL_EXCLUSION_PATTERNS` (tuple of keyword-AND groups) and individual recipe pages are parsed by the `hhursev` `recipe_scrapers` lib. Site HTML structures drift — a failing site usually means its `regex` needs updating. Failures are caught and recorded in `failed_recipes`, never fatal (this runs unattended).

### Email + website publish

`head.html` (repo root) supplies the email's `<head>`/CSS; `html_generator` appends `<body>` cards. `website_publisher` extracts that `<body>`, re-wraps it in the external website's template (`WEBSITE_REPO_PATH` env, with `templates/navbar.html`), writes `meals.html`, and git commit/pushes to that separate repo. Skipped if `WEBSITE_REPO_PATH` is unset or in debug mode.

## Configuration

`.env` (required): `SENDER`, `PASSWD` (Gmail app password), `BCC` (comma-separated recipients). Optional: `WEBSITE_REPO_PATH`.

## Conventions

- mypy strict + ruff + black (line length 88) are enforced in CI. Newer modules (`config`, `file_utils`, `recipe_selector`, `main`, `website_publisher`) are fully typed with docstrings; older ones (`web_scraper`, `html_generator`, `email_sender`, `recipe_processor`) are looser — match the style of the file you're editing.
- Errors in the pipeline are logged and routed to `_send_error_notification` (emails the traceback to SENDER) rather than crashing silently; business logic avoids `sys.exit`.
- Tests are characterization/baseline tests (`*_baseline.py`) capturing current behavior — run them before and after refactors.
