#!/usr/bin/env python3

# IMPORT STANDARD MODULES
import argparse
import json
import os
import random
import re
import smtplib
import ssl
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

# IMPORT THIRD-PARTY MODULES
import requests
from dotenv import load_dotenv
from recipe_scrapers import scrape_html
from tqdm import tqdm

# IMPORT LISTS
from lists import veggies, websites

# VERSION TAG
version = 15.1


@dataclass
class Website:
    title: str
    regex: str
    entree_page_url: str
    side_page_url: str


@dataclass
class Recipe:
    url: str
    title: Optional[str] = None
    host: Optional[str] = None
    site_name: Optional[str] = None
    ingredients: Optional[list[str]] = None
    instructions: Optional[list[str]] = None
    image: Optional[str] = None
    meal_type: Optional[str] = None  # entree or side
    protein_type: Optional[str] = None  # seafood or landfood
    has_veggies: Optional[bool] = False
    date_retrieved: Optional[str] = None
    used: Optional[bool] = False
    date_sent: Optional[str] = None


def check_debug_mode() -> bool:
    """Check if user passed a debug flag when running script."""
    parser = argparse.ArgumentParser(description="Check for debug mode")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    if args.debug:
        print("Debug mode detected")
        return True
    return False


def list_debug_options() -> dict:
    """List websites for debugging.

    If in debug mode, tell the user what keys (website title) are in the
    dictonary along with their index.
    """
    print("The websites list supports the following sites:")
    for n, website in enumerate(websites):
        # note we increment by 1 to make output more user-friendly
        print(f"{n + 1}\t{website}")
    while True:
        try:
            # prompt user to enter the index of the list they wish to debug
            number = int(input("Which website would you like to debug? (#) "))
            # only accept input that would fall within the indicies of
            # the dictionary. Recall the increment from above
            if 0 < number < len(websites) + 1:
                # account for the increment when saving user selection
                selection = list(websites)[number - 1]
                break
            raise ValueError
        except ValueError:
            print("I'm sorry, that wasn't a valid number.")
    # show user what they've selected before proceeding
    print(f"You've selectected to debug {selection}.")
    print("The dictionary entry is:")
    print(json.dumps(websites[selection], indent=4))
    return websites[selection]


def save_json(filename: str, data: dict) -> None:
    """Save json data at filename."""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def load_json(filename: str) -> dict:
    """Open json data from filename."""
    try:
        with open(filename) as f:
            data = json.load(f)
        if len(data) == 0:
            raise FileNotFoundError
    except FileNotFoundError:
        print(f"Did not find {filename}, returning empty dictionary")
        return {}
    return data


def build_website_class(website: dict) -> Website:
    built_website_class = Website(**website)
    return built_website_class


def is_file_old(filename: str, old: int = 12, age: float = 12.0) -> bool:
    """Check if a file is older than desireable age.

    filename:   File to check
    old:        Maximum permissible age of file
    age:        Current file age, if file does not exist, defaults to 12h old
    """
    if os.path.isfile(filename):  # check that the file exists
        age = os.stat(filename).st_mtime
        age = (time.time() - age) / 3600  # convert age from seconds to hours
    return age >= old


def main():
    """It all starts here."""
    # START TIMER
    start_time = time.time()

    # SET FILENAME CONSTANTS
    websites_filename = "websites.json"
    entrees_filename = "entrees.json"
    sides_filename = "sides.json"

    debug_mode = check_debug_mode()

    if debug_mode:
        selection = list_debug_options()
        websites = {"debugging": selection}  # redifine websites list for debug session
        unused_main_recipes, unused_side_recipes = {}, {}
        failed_recipes, used_recipes = {}, {}

    # LOAD PREVIOUSLY COLLECTED DATA
    if not debug_mode:
        print("Loading previously collected data")
        entrees = load_json(entrees_filename)
        sides = load_json(sides_filename)

    # CHECK RECENCY OF PREVIOUSLY COLLECTED DATA
    if is_file_old(entrees_filename):
        print(entrees_filename, "is old, getting fresh data")
        # SCRAPE FRESH DATA IF EXISTING DATA IS OLD
        entrees, sides = get_fresh_data(websites)
        if not debug_mode:
            save_json(entrees_filename, entrees)
            save_json(sides_filename, sides)

    # SORT BY PROTEIN AND RETURN LIST OF THREE RANDOM MEALS
    print("Getting meals with select proteins at random")
    randomized_meals = get_random_proteins(entrees)

    # ENSURE MEALS HAVE ADEQUATE VEGGIES OR ADD A SIDE
    print("Checking for veggies")
    meals = veggie_checker(randomized_meals, unused_side_recipes)

    # PRETTYIFY THE MEALS INTO EMAILABLE HTML BODY
    print("Prettifying meals into HTML")
    pretty = prettify(meals, start_time)

    if not debug_mode:
        # SEND EMAIL
        print("Emailing recipients")
        mailer(pretty, debug_mode)

        # UPDATE THE RESOURCE FILES BEFORE SAVING OUT
        date = datetime.today().strftime("%Y-%m-%d")
        for meal in meals:
            try:
                url = next(iter(meal["obj"]))
                used_recipes[url] = date
                if url in unused_main_recipes:
                    del unused_main_recipes[url]
                elif url in unused_side_recipes:
                    del unused_side_recipes[url]
                else:
                    raise KeyError
            except KeyError:
                print(f"{url} was not in the main or side lists, so not removing")
        print(
            f"main {len(unused_main_recipes)} final\nside {len(unused_side_recipes)} final"
        )

        # SAVE OUT DICTIONARIES AS FILES FOR REUSE
        print("Saving out files")
        save_json(unused_mains_filename, unused_main_recipes)
        save_json(unused_sides_filename, unused_side_recipes)
        save_json(failed_filename, failed_recipes)
        save_json(used_filename, used_recipes)


if __name__ == "__main__":
    main()
