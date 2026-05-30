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
    "VERSION",
    "UNUSED_MAINS_FILENAME",
    "UNUSED_SIDES_FILENAME",
    "FAILED_FILENAME",
    "SCRAPE_FLUSH_INTERVAL",
    "USED_FILENAME",
    "FILE_AGE_THRESHOLD",
    "HEADERS",
    "DEBUG_TIMEOUT",
    "NORMAL_TIMEOUT",
    "SMTP_SERVER",
    "SMTP_PORT",
    "EMAIL_SENDER",
    "EMAIL_PASSWORD",
    "EMAIL_BCC",
    "REQUIRED_RECIPE_KEYS",
    "URL_EXCLUSION_PATTERNS",
    "URL_FIX_PREFIX",
    "URL_FIX_DOMAIN",
    "SEAFOOD_PROTEINS",
    "LANDFOOD_PROTEINS",
    "LANDFOOD_COUNT_WITH_SEAFOOD",
    "SEAFOOD_COUNT",
    "SUBJECT",
    "LANDFOOD_COUNT_NO_SEAFOOD",
    "VEGGIES",
    "WEBSITE_REPO_PATH",
]

# VERSION TAG
VERSION: Final[float] = 16.0

# Email Subject Line
SUBJECT: Final[str] = "Weekly Meals"

# FILENAME CONSTANTS
UNUSED_MAINS_FILENAME: Final[str] = "unused_mains_recipes.json"
UNUSED_SIDES_FILENAME: Final[str] = "unused_sides_recipes.json"
FAILED_FILENAME: Final[str] = "failed_recipes.json"
USED_FILENAME: Final[str] = "used_recipes.json"

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
WEBSITE_REPO_PATH: Final[str | None] = os.getenv("WEBSITE_REPO_PATH")

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
