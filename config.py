"""Configuration and constants for the recipe scraper."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# VERSION TAG
VERSION = 15.5

# FILENAME CONSTANTS
UNUSED_MAINS_FILENAME = "unused_mains_recipes.json"
UNUSED_SIDES_FILENAME = "unused_sides_recipes.json"
FAILED_FILENAME = "failed_recipes.json"
USED_FILENAME = "used_recipes.json"

# FILE AGE THRESHOLD (in hours)
FILE_AGE_THRESHOLD = 12

# HTTP HEADERS
HEADERS = {
    "user-agent": "mozilla/5.0 (macintosh; intel mac os x "
    "10_11_5) applewebkit/537.36 (khtml, like gecko) "
    "chrome/50.0.2661.102 safari/537.36"
}

# TIMEOUT SETTINGS
DEBUG_TIMEOUT = 20
NORMAL_TIMEOUT = 9

# EMAIL SETTINGS
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_SENDER = os.getenv("SENDER")
EMAIL_PASSWORD = os.getenv("PASSWD")
EMAIL_BCC = os.getenv("BCC")

# REQUIRED RECIPE KEYS
REQUIRED_RECIPE_KEYS = [
    "title",
    "site_name",
    "host",
    "ingredients",
    "instructions",
    "image",
]

# URL CLEANUP PATTERNS
# URLs containing these patterns will be filtered out
URL_EXCLUSION_PATTERNS = [
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
]

# URL FIXES
# Patterns for fixing malformed URLs
URL_FIX_PREFIX = "/recipes/"
URL_FIX_DOMAIN = "https://www.leanandgreenrecipes.net"

# PROTEIN CATEGORIZATION
# Ingredients that classify a recipe as seafood
SEAFOOD_PROTEINS = [
    "scallops",
    "salmon",
    "shrimp",
    "tuna",
]

# Ingredients that classify a recipe as land-based protein
LANDFOOD_PROTEINS = [
    "chickpea",
    "chicken",
    "turkey",
    "pork",
    "tofu",
]

# MEAL SELECTION SETTINGS
# Number of land-based meals to send when seafood is available
LANDFOOD_COUNT_WITH_SEAFOOD = 2
# Number of seafood meals to send when available
SEAFOOD_COUNT = 1
# Total number of meals to send when no seafood available
LANDFOOD_COUNT_NO_SEAFOOD = 3

# List of key veggies that we want in a meal
VEGGIES = [
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
]
