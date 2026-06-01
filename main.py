#!/usr/bin/env python3
"""Recipe emailer main entry point.

This program scrapes recipes from configured websites and emails
a curated selection to recipients each week.
"""

from __future__ import annotations

import html
import logging
import sys
import time
import traceback
from datetime import date, datetime
from logging.handlers import RotatingFileHandler
from typing import Any

from config import (
    FAILED_FILENAME,
    FILE_AGE_THRESHOLD,
    HEALTH_SUBJECT,
    SITE_HEALTH_FILENAME,
    SUBJECT,
    UNUSED_MAINS_FILENAME,
    UNUSED_SIDES_FILENAME,
    USED_FILENAME,
    VEGGIES,
    WEBSITE_REPO_PATH,
)
from debug_utils import is_debug_mode, select_website_interactively
from email_sender import send_email
from file_utils import is_file_old, load_json, save_json
from html_generator import generate_html_email
from recipe_processor import fetch_fresh_recipes
from recipe_selector import ensure_veggies, select_random_proteins
from seasonal_selection import final_score, season_fit
from seasonal_tagging import ensure_recipe_tagged
from site_health import (
    build_report,
    has_something_to_report,
    record_run,
    render_health_email,
)
from website_publisher import publish_meals_page
from websites import WEBSITES

__all__ = ["main"]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        # Self-capping: rotate at ~1 MB, keep 3 old files (~4 MB max total).
        RotatingFileHandler("recipe_emailer.log", maxBytes=1_000_000, backupCount=3),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Main execution function with comprehensive error handling."""
    start_time = time.time()

    try:
        logger.info("=" * 70)
        logger.info(f"Recipe Emailer started at {datetime.now()}")
        logger.info("=" * 70)

        # Check for debug mode
        debug_mode = is_debug_mode()

        # Load or initialize data
        context = _initialize_context(debug_mode)

        # Fetch fresh recipes if needed
        if context["needs_fresh_data"]:
            _fetch_and_update_recipes(context, debug_mode)
            if not debug_mode:
                _monitor_site_health(context)

        # Tag newly-scraped recipes for seasonal selection (normal runs only)
        if not debug_mode:
            _tag_new_recipes(context)

        # Select and prepare meals
        meals = _select_and_prepare_meals(context)

        # Generate and send email
        html_content = _generate_and_send_email(context, meals, start_time, debug_mode)

        # Publish meals page to website (skip in debug mode)
        if not debug_mode:
            _publish_meals_to_website(html_content)

        # Update tracking data (skip in debug mode)
        if not debug_mode:
            _update_tracking_data(context, meals)

        elapsed = time.time() - start_time
        logger.info(f"✓ Process completed successfully in {elapsed:.2f}s")

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        _send_error_notification(e)
        sys.exit(1)


def _initialize_context(debug_mode: bool) -> dict[str, Any]:
    """Initialize application context with configuration and data."""
    if debug_mode:
        logger.info("Running in DEBUG mode")
        selected_site = select_website_interactively(WEBSITES)

        return {
            "websites": {"debug_site": selected_site},
            "unused_mains": {},
            "unused_sides": {},
            "failed_recipes": {},
            "used_recipes": {},
            "needs_fresh_data": True,
        }

    # Normal mode: load existing data
    logger.info("Loading existing recipe data")
    unused_mains, mains_created = load_json(UNUSED_MAINS_FILENAME)
    unused_sides, sides_created = load_json(UNUSED_SIDES_FILENAME)
    failed_recipes, _ = load_json(FAILED_FILENAME)
    used_recipes, _ = load_json(USED_FILENAME)

    # Determine if fresh data is needed
    needs_fresh = (
        mains_created
        or sides_created
        or is_file_old(UNUSED_MAINS_FILENAME, FILE_AGE_THRESHOLD)
    )

    if needs_fresh:
        reason = (
            "files newly created"
            if (mains_created or sides_created)
            else f"data older than {FILE_AGE_THRESHOLD}h"
        )
        logger.info(f"Fresh data needed: {reason}")

    return {
        "websites": WEBSITES,
        "unused_mains": unused_mains,
        "unused_sides": unused_sides,
        "failed_recipes": failed_recipes,
        "used_recipes": used_recipes,
        "needs_fresh_data": needs_fresh,
    }


def _fetch_and_update_recipes(context: dict[str, Any], debug_mode: bool) -> None:
    """Fetch fresh recipes and update context."""
    logger.info("Fetching fresh recipe data...")

    updated_mains, updated_sides, run_outcomes = fetch_fresh_recipes(
        context["websites"],
        context["unused_mains"],
        context["unused_sides"],
        context["used_recipes"],
        context["failed_recipes"],
        debug_mode=debug_mode,
    )

    context["unused_mains"] = updated_mains
    context["unused_sides"] = updated_sides
    context["run_outcomes"] = run_outcomes

    # Save updated data (skip in debug mode)
    if not debug_mode:
        save_json(UNUSED_MAINS_FILENAME, updated_mains)
        save_json(UNUSED_SIDES_FILENAME, updated_sides)
        logger.info("Saved updated recipe data")


def _monitor_site_health(context: dict[str, Any]) -> None:
    """Record per-site scrape outcomes and email the maintainer on problems.

    Records this run's outcomes to SITE_HEALTH_FILENAME and, if any site's
    regex looks broken / a site is unreachable / a site is flaky, emails a
    summary to SENDER. Never raises — a monitoring failure must not break the
    recipe run.
    """
    try:
        outcomes = context.get("run_outcomes", [])
        if not outcomes:
            return

        health_data, _ = load_json(SITE_HEALTH_FILENAME)
        run_date = datetime.now().strftime("%Y-%m-%d")
        record_run(health_data, outcomes, run_date)
        save_json(SITE_HEALTH_FILENAME, health_data)

        report = build_report(health_data)
        if has_something_to_report(report):
            logger.info("Site-health issues found; emailing maintainer")
            send_email(
                render_health_email(report),
                debug_mode=True,  # routes Bcc to SENDER only
                subject=HEALTH_SUBJECT,
            )
        else:
            logger.info("Site health all clear; no maintainer email")
    except Exception as e:
        logger.exception(f"Site-health monitoring failed: {e}")


def _tag_new_recipes(context: dict[str, Any]) -> None:
    """Add seasonal/oven tags to every untagged recipe. Never raises.

    Seasonal inference is now instant (pure-numpy student model), so every
    untagged recipe across mains+sides is tagged in a single run. Saves only
    the files it changed. A tagging failure logs and is swallowed so it cannot
    break the recipe run.
    """
    try:
        tagged = 0
        mains_changed = False
        sides_changed = False

        for filename_key, changed_flag in (
            ("unused_mains", "mains"),
            ("unused_sides", "sides"),
        ):
            for recipe in context[filename_key].values():
                if ensure_recipe_tagged(recipe):
                    tagged += 1
                    if changed_flag == "mains":
                        mains_changed = True
                    else:
                        sides_changed = True

        if mains_changed:
            save_json(UNUSED_MAINS_FILENAME, context["unused_mains"])
        if sides_changed:
            save_json(UNUSED_SIDES_FILENAME, context["unused_sides"])
        logger.info(f"Seasonal tagging: tagged {tagged} new recipe(s)")
    except Exception as e:
        logger.exception(f"Seasonal tagging failed: {e}")


def _select_and_prepare_meals(context: dict[str, Any]) -> list[dict[str, Any]]:
    """Select seasonally-weighted meals and ensure they have vegetables."""
    today = datetime.now().date()

    logger.info("Selecting meals with balanced proteins")
    selected_meals = select_random_proteins(context["unused_mains"], today)

    logger.info("Ensuring meals have adequate vegetables")
    prepared_meals = ensure_veggies(
        selected_meals,
        context["unused_sides"],
        VEGGIES,
        today,
    )

    _log_selection_scores(prepared_meals, today)
    logger.info(f"Prepared {len(prepared_meals)} meal components")
    return prepared_meals


def _log_selection_scores(meals: list[dict[str, Any]], today: date) -> None:
    """Log each pick's seasonality / oven_use / scores (for troubleshooting).

    The chosen recipes are removed from the unused files after a run, so this is
    the only durable record of why a given meal was picked.
    """
    for meal in meals:
        obj = meal["obj"]
        url = next(iter(obj))
        recipe = obj[url]
        seasonality = recipe.get("seasonality")
        logger.info(
            "selected %s [%s]: seasonality=%s oven_use=%s season_fit=%.3f "
            "final_score=%.3f",
            url,
            meal["type"],
            seasonality if seasonality is not None else "untagged(neutral)",
            recipe.get("oven_use", "n/a"),
            season_fit(recipe, today),
            final_score(recipe, today),
        )


def _generate_and_send_email(
    context: dict[str, Any],
    meals: list[dict[str, Any]],
    start_time: float,
    debug_mode: bool,
) -> str:
    """Generate HTML and send email."""
    logger.info("Generating HTML email content")
    html_content = generate_html_email(
        meals,
        start_time,
        len(context["unused_mains"]),
        len(context["unused_sides"]),
    )

    logger.info("Sending email")
    send_email(html_content, debug_mode, SUBJECT)
    return html_content


def _update_tracking_data(context: dict[str, Any], meals: list[dict[str, Any]]) -> None:
    """Update used recipes and remove them from unused lists."""
    date_str = datetime.now().strftime("%Y-%m-%d")

    for meal_item in meals:
        meal_obj = meal_item["obj"]
        url = next(iter(meal_obj))

        # Mark as used
        context["used_recipes"][url] = date_str

        # Remove from unused lists
        if url in context["unused_mains"]:
            del context["unused_mains"][url]
        elif url in context["unused_sides"]:
            del context["unused_sides"][url]
        else:
            logger.warning(f"URL {url} not found in unused lists")

    # Save updated tracking data
    save_json(UNUSED_MAINS_FILENAME, context["unused_mains"])
    save_json(UNUSED_SIDES_FILENAME, context["unused_sides"])
    save_json(FAILED_FILENAME, context["failed_recipes"])
    save_json(USED_FILENAME, context["used_recipes"])

    logger.info(
        f"Updated tracking: {len(context['unused_mains'])} mains, "
        f"{len(context['unused_sides'])} sides remaining"
    )


def _publish_meals_to_website(html_content: str) -> None:
    """Publish meals page to website repo with error notification on failure."""
    if not WEBSITE_REPO_PATH:
        logger.warning("WEBSITE_REPO_PATH not set, skipping website publish")
        return

    try:
        publish_meals_page(html_content, WEBSITE_REPO_PATH)
    except Exception as e:
        logger.exception(f"Failed to publish meals page: {e}")
        _send_error_notification(e, subject="Recipe Emailer - Website Publish Error")


def _send_error_notification(
    error: Exception, subject: str = "Recipe Emailer Error"
) -> None:
    """Send email notification about errors."""
    try:
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        tb_str = "".join(tb)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_html = f"""
        <html>
        <body>
        <h1>{html.escape(subject)}</h1>
        <p>An error occurred at <strong>{timestamp}</strong>:</p>
        <pre>{html.escape(f"{type(error).__name__}: {error}")}</pre>
        <h2>Traceback</h2>
        <pre>{html.escape(tb_str)}</pre>
        </body>
        </html>
        """
        send_email(
            error_html,
            debug_mode=True,  # Always send errors to sender only
            subject=subject,
        )
    except Exception as email_error:
        logger.error(f"Failed to send error notification: {email_error}")


if __name__ == "__main__":
    main()
