"""Configuration and constants for the recipe scraper.

This module centralizes all configuration values, environment variables,
and constants used throughout the application.
"""

from __future__ import annotations

import os
from typing import Final

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

__all__ = [
    "DEBUG_TIMEOUT",
    "EMAIL_BCC",
    "EMAIL_PASSWORD",
    "EMAIL_SENDER",
    "FAILED_FILENAME",
    "FALL_CENTER",
    "FILE_AGE_THRESHOLD",
    "HEADERS",
    "HEALTH_SUBJECT",
    "HEAT_WEIGHT",
    "LANDFOOD_COUNT_NO_SEAFOOD",
    "LANDFOOD_COUNT_WITH_SEAFOOD",
    "LANDFOOD_PROTEINS",
    "MIN_SCORE",
    "NORMAL_TIMEOUT",
    "OLLAMA_HOST",
    "OLLAMA_TIMEOUT",
    "PUBLISH_PAGE_FILENAME",
    "REQUIRED_RECIPE_KEYS",
    "SCRAPE_FLUSH_INTERVAL",
    "SEAFOOD_COUNT",
    "SEAFOOD_PROTEINS",
    "SEASONAL_LABELS_FILENAME",
    "SEASONAL_MODEL",
    "SEASONAL_MODEL_FILENAME",
    "SELECTION_SHARPNESS",
    "SITE_HEALTH_FILENAME",
    "SMTP_PORT",
    "SMTP_SERVER",
    "SPRING_CENTER",
    "SUBJECT",
    "SUMMER_CENTER",
    "UNUSED_MAINS_FILENAME",
    "UNUSED_SIDES_FILENAME",
    "URL_EXCLUSION_PATTERNS",
    "URL_FIX_DOMAIN",
    "URL_FIX_PREFIX",
    "USED_FILENAME",
    "VEGGIES",
    "VERSION",
    "WINTER_CENTER",
]

# VERSION TAG
VERSION: Final[float] = 17.0

# Email Subject Line
SUBJECT: Final[str] = "Weekly Meals"

# FILENAME CONSTANTS
UNUSED_MAINS_FILENAME: Final[str] = "unused_mains_recipes.json"
UNUSED_SIDES_FILENAME: Final[str] = "unused_sides_recipes.json"
FAILED_FILENAME: Final[str] = "failed_recipes.json"
USED_FILENAME: Final[str] = "used_recipes.json"
SITE_HEALTH_FILENAME: Final[str] = "site_health.json"
HEALTH_SUBJECT: Final[str] = "Recipe Emailer — Site Health"

# Standalone HTML page written each run for GitHub Pages publishing. cook.sh
# commits + pushes this file to the gh-pages branch (see README).
PUBLISH_PAGE_FILENAME: Final[str] = "index.html"

# FILE AGE THRESHOLD (in hours)
FILE_AGE_THRESHOLD: Final[int] = 12

# HTTP HEADERS
HEADERS: Final[dict[str, str]] = {
    "user-agent": (
        "mozilla/5.0 (macintosh; intel mac os x 10_11_5) "
        "applewebkit/537.36 (khtml, like gecko) "
        "chrome/50.0.2661.102 safari/537.36"
    )
}

# TIMEOUT SETTINGS (in seconds)
DEBUG_TIMEOUT: Final[int] = 20
NORMAL_TIMEOUT: Final[int] = 9

# EMAIL SETTINGS
SMTP_SERVER: Final[str] = "smtp.gmail.com"
SMTP_PORT: Final[int] = 465
EMAIL_SENDER: Final[str | None] = os.getenv("SENDER")
EMAIL_PASSWORD: Final[str | None] = os.getenv("PASSWD")
EMAIL_BCC: Final[str | None] = os.getenv("BCC")

# REQUIRED RECIPE KEYS
REQUIRED_RECIPE_KEYS: Final[tuple[str, ...]] = (
    "title",
    "site_name",
    "host",
    "ingredients",
    "instructions",
    "image",
)

# URL CLEANUP PATTERNS
# URLs containing these patterns will be filtered out
URL_EXCLUSION_PATTERNS: Final[tuple[tuple[str, ...], ...]] = (
    ("plan",),
    ("eggplant",),
    ("dishes", "/recipes/"),
    ("dishes", "best"),
    ("black", "friday"),
    ("how", "use"),
    ("dishes",),
    ("ideas",),
    ("30-whole30-meals-in-30-minutes",),
    ("guide",),
)

# URL FIXES
# Patterns for fixing malformed URLs
URL_FIX_PREFIX: Final[str] = "/recipes/"
URL_FIX_DOMAIN: Final[str] = "https://www.leanandgreenrecipes.net"

# PROTEIN CATEGORIZATION
# Ingredients that classify a recipe as seafood
SEAFOOD_PROTEINS: Final[tuple[str, ...]] = (
    "scallops",
    "salmon",
    "shrimp",
    "tuna",
)

# Ingredients that classify a recipe as land-based protein
LANDFOOD_PROTEINS: Final[tuple[str, ...]] = (
    "chickpea",
    "chicken",
    "turkey",
    "pork",
    "tofu",
)

# MEAL SELECTION SETTINGS
# Number of land-based meals to send when seafood is available
LANDFOOD_COUNT_WITH_SEAFOOD: Final[int] = 2
# Number of seafood meals to send when available
SEAFOOD_COUNT: Final[int] = 1
# Total number of meals to send when no seafood available
LANDFOOD_COUNT_NO_SEAFOOD: Final[int] = 3

# List of key veggies that we want in a meal
VEGGIES: Final[tuple[str, ...]] = (
    "acorn squash",
    "artichoke",
    "arugula",
    "asparagus",
    "bell pepper",
    "broccoli",
    "broccolini",
    "brussel sprouts",
    "butternut squash",
    "cabbage",
    "carrot",
    "cannellini",
    "cauliflower",
    "celery",
    "cucumber",
    "eggplant",
    "garbanzo",
    "green bean",
    "kale",
    "kohlrabi",
    "lettuce",
    "mushroom",
    "nori",
    "ogonori",
    "okra",
    "peas",
    "potato",
    "radish",
    "snap pea",
    "soybean",
    "spinach",
    "squash",
    "yam",
    "zucchini",
)

# How often (in scraped URLs) to flush recipe progress to disk during scraping.
SCRAPE_FLUSH_INTERVAL: Final[int] = 100

# SEASONAL AI SELECTION SETTINGS
# Ollama endpoint + model for seasonal scoring (small local model on the Pi 4).
OLLAMA_HOST: Final[str] = os.getenv("OLLAMA_HOST", "http://localhost:11434")
SEASONAL_MODEL: Final[str] = os.getenv("SEASONAL_MODEL", "qwen2.5:1.5b")
OLLAMA_TIMEOUT: Final[int] = 60

# How strongly oven-use vs. season weighting tilts the final score.
HEAT_WEIGHT: Final[float] = 0.5
# Positive floor so weighted-random never sees a zero/negative weight.
MIN_SCORE: Final[float] = 0.01
# Exponent applied to selection weights before weighted-random sampling. >1
# sharpens the bias so off-season / oven-heavy picks are chosen less often
# (e.g. 3.0 makes a 0.8-score recipe ~50x likelier than a 0.2-score one).
SELECTION_SHARPNESS: Final[float] = 3.0

# Northern-Hemisphere season centers as day-of-year (approx. solstices/equinoxes).
SPRING_CENTER: Final[int] = 79  # ~Mar 20
SUMMER_CENTER: Final[int] = 172  # ~Jun 21
FALL_CENTER: Final[int] = 265  # ~Sep 22
WINTER_CENTER: Final[int] = 355  # ~Dec 21

# Distilled seasonality student model (pure-numpy inference on the Pi) and the
# teacher label file used to train it (desktop-only).
SEASONAL_MODEL_FILENAME: Final[str] = "seasonal_model.json"
SEASONAL_LABELS_FILENAME: Final[str] = "seasonal_labels.json"
