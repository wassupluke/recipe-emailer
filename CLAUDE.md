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

# Quality gate (mirrors CI's Code Quality + Security jobs)
mypy . --strict && ruff check . && black --check . && bandit -c pyproject.toml -r .

# Production entry point (used by cron)
./cook.sh   # cd, activate .venv, python3 main.py >> cronjob.log
```

Python ≥3.11. Dev tooling installed via `pip install -e ".[dev]"`.

## Architecture

Flat module layout (no package) — every module is a top-level file importing siblings directly. `main.py` orchestrates a linear pipeline; each stage lives in its own module:

```
scrape (recipe_processor → web_scraper)
  → record site health (site_health.record_run)
  → tag new recipes (seasonal_tagging.ensure_recipe_tagged)
  → select proteins, seasonally weighted (recipe_selector.select_random_proteins)
  → ensure veggies / add sides (recipe_selector.ensure_veggies)
  → render (html_generator.generate_html_email)
  → send (email_sender.send_email)
  → write publish page (website_publisher.write_publish_page → index.html)
  → update tracking JSON (file_utils.save_json)
```

`config.py` centralizes all constants + env vars; nearly every module imports from it. `main.py` passes a single `context` dict between its private `_*` helpers.

### State lives in committed JSON files

The four `*_recipes.json` files in the repo root **are the database** and are tracked in git (see commits like "update DBs"). They are keyed by recipe URL:

- `unused_mains_recipes.json` / `unused_sides_recipes.json` — scraped-but-not-yet-sent recipes
- `used_recipes.json` — `{url: date_sent}`, prevents repeats
- `failed_recipes.json` — `{url: failure_reason}`, URLs to skip

On each run, `unused_mains` is re-scraped only if it's newly created or older than `FILE_AGE_THRESHOLD` (12h). When a recipe is emailed it moves from an `unused_*` file into `used_recipes`. Debug mode never writes these files.

Also tracked: `seasonal_labels.json` (teacher labels) and `seasonal_model.json` (trained student artifact). `site_health.json` is untracked runtime state (see Site health below).

### Two recipe data shapes (easy to confuse)

1. **Raw recipe** — the value stored in the JSON files: a dict from `recipe_scrapers.scrape_html(...).to_json()` with keys `title`, `ingredients`, `instructions`, `image`, `site_name`, `host`, etc. (`REQUIRED_RECIPE_KEYS` in config). A "recipe item" wraps one as `{url: recipe_dict}`.
2. **Meal item** — what `ensure_veggies` produces and what `html_generator`/tracking consume: `{"type": ..., "obj": {url: recipe_dict}}` where `type` is `single_main`, `combo_main`, or `combo_side`. Unwrap the recipe with `info["obj"][next(iter(info["obj"]))]`.

### Selection logic (recipe_selector.py)

Recipes are categorized seafood vs. landfood by substring-matching `SEAFOOD_PROTEINS`/`LANDFOOD_PROTEINS` against ingredient strings. `_select_meal_mix` sends 2 land + 1 seafood when seafood exists, else 3 land, else raises `InsufficientRecipesError`. Within each category, picks are weighted-random on `seasonal_selection.final_score` (not uniform). A main lacking any `VEGGIES` ingredient gets a seasonally-weighted side dish appended (producing the `combo_*` pair). `main._log_selection_scores` logs why each pick won — the only durable record, since chosen recipes leave the `unused_*` files.

### Seasonal scoring (teacher → student distillation)

Runtime selection prefers in-season recipes without any network/LLM dependency:

- Each recipe in `unused_*` carries cached tags: `seasonality` ({spring,summer,fall,winter} scores) and `oven_use` (rule-based keyword scan). `seasonal_tagging.ensure_recipe_tagged` adds them once per recipe during the pipeline; it never raises (falls back to neutral 0.5).
- `seasonal_model.py` is numpy-only inference over `seasonal_model.json`, a TF-IDF + ridge "student" artifact. Its `tokenize`/`recipe_text` are imported by the training script so train/inference featurization stay identical.
- `seasonal_selection.py` is pure date math: blends season weights by day-of-year distance from `*_CENTER` constants, mixes in a winter↔summer heat preference vs `oven_use` (`HEAT_WEIGHT`), and provides `weighted_sample`.

Offline scripts (run by hand, not by cron): `seasonal_label.py` labels recipes via Ollama on a GPU desktop (the teacher) → `seasonal_labels.json`; `train_seasonal_model.py` fits the student with scikit-learn → `seasonal_model.json`; `backfill_seasonality.py` one-off tags the existing backlog using the local student model. All are safe to re-run; labeling and backfill resume where they left off.

### Site health (site_health.py)

After each scrape, every (website, course) listing page's outcome is classified ok / regex-broken / unreachable and appended to `site_health.json` (a rolling window of the last `WINDOW_SIZE` runs). If any site is currently broken/unreachable, or a currently-OK site failed at least `FLAKY_THRESHOLD` times within the window, a report email goes to SENDER only — this is how the maintainer learns a site's `regex` drifted.

### Scraping (websites.py + web_scraper.py)

`WEBSITES` maps a site name → `{regex, "main course" url, "side dish" url}`. Each site's index pages are fetched and `regex` extracts individual recipe URLs. URLs are filtered through `URL_EXCLUSION_PATTERNS` (tuple of keyword-AND groups) and individual recipe pages are parsed by the `hhursev` `recipe_scrapers` lib. Site HTML structures drift — a failing site usually means its `regex` needs updating. Failures are caught and recorded in `failed_recipes`, never fatal (this runs unattended).

### Email + page publish

`head.html` (repo root) supplies the email's `<head>`/CSS; `html_generator` produces a complete self-contained HTML document. `website_publisher.write_publish_page` writes that same HTML verbatim to `PUBLISH_PAGE_FILENAME` (`index.html`); `cook.sh` then commits + pushes it to the `gh-pages` branch via a throwaway git worktree (so the main working tree / recipe JSONs are untouched). The write step is skipped in debug mode; the push is a self-contained, deletable block in `cook.sh`. `index.html` is gitignored on `main`.

## Configuration

`.env` (required): `SENDER`, `PASSWD` (Gmail app password), `BCC` (comma-separated recipients).

## Conventions

- mypy strict + ruff + black (line length 88) are enforced in CI. Newer modules (`config`, `file_utils`, `recipe_selector`, `main`, `website_publisher`, `site_health`, the `seasonal_*` family) are fully typed with docstrings; older ones (`web_scraper`, `html_generator`, `email_sender`, `recipe_processor`, `debug_utils`) are looser — match the style of the file you're editing.
- Errors in the pipeline are logged and routed to `_send_error_notification` (emails the traceback to SENDER) rather than crashing silently; business logic avoids `sys.exit`.
- Tests are characterization/baseline tests (`*_baseline.py`) capturing current behavior — run them before and after refactors.
