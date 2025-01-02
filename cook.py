#!/usr/bin/env python3

"""A program I wrote to save my wife time and headache.

This program grabs recipes from all her favorite sites
and sends her a few to make each week. Now she doesn't
have to spend her time looking up what to make, it's all
automagic!
"""

# IMPORT STANDARD MODULES
import argparse
import json
import logging
import os
import random
import re
import smtplib
import ssl
import sys
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# IMPORT THIRD-PARTY MODULES
import requests
import toml
from dotenv import load_dotenv
from pandas import concat, json_normalize, read_pickle
from recipe_scrapers import scrape_html
from tqdm import tqdm

# IMPORT LISTS
from veggies import veggies

# VERSION TAG
version = 16.0

# FILENAME CONSTANTS
unused_mains_filename = "unused_mains_recipes.json"
unused_sides_filename = "unused_sides_recipes.json"
failed_filename = "failed_recipes.json"
used_filename = "used_recipes.json"
database = "master_data.pkl"
websites_filename = "websites.toml"


def check_debug_mode() -> bool:
    """Check for debug mode or default to full mode."""
    parser = argparse.ArgumentParser(description="Check for debug mode")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    if args.debug:
        print("Debug mode detected")
        return True
    return False


def debug_list_selection() -> dict:
    """When in debug mode, tell user what website titles are in the dictonary."""
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
    """Save json data to a file."""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def load_json(filename: str) -> dict:
    """Return dictionary of json data from a file."""
    try:
        with open(filename) as f:
            data = json.load(f)
        if len(data) == 0:
            raise FileNotFoundError
    except FileNotFoundError:
        print(f"Did not find {filename}, returning empty dictionary")
        return {}
    return data


def load_pickle(filename: str):
    """Return DataFrame from file."""
    return read_pickle(filename)


def save_pickle(filename: str, data) -> None:
    """Save DataFrame to file."""
    data.to_pickle(filename)


def save_toml(filename: str, data: dict) -> None:
    """Save TOML data to file."""
    with open(filename, "w") as f:
        toml.dump(data, f)


def load_toml(filename: str) -> dict | None:
    """Return TOML data from file."""
    try:
        with open(filename) as f:
            data = toml.load(f)
        if len(data) == 0:
            raise FileNotFoundError
    except FileNotFoundError:
        print(f"{filename} is empty or missing, returning None.")
        return None
    return data


def is_file_old(filename: str, old: int = 12, age: int = 12) -> bool:
    """Check if a file is older than a certain age."""
    if os.path.isfile(filename):  # check that the file exists
        age = int(os.stat(filename).st_mtime)
        age = int((time.time() - age) / 3600)  # convert seconds to hours
    return age >= old


def get_fresh_data(
    websites: dict[str, dict[str, str]], df
) -> tuple[dict[str, dict], dict[str, dict]]:
    """GET LATEST URLS FROM HTML, separating entrees and sides."""
    main_urls, side_urls = [], []
    print("Getting website HTML")
    for site_info in tqdm(websites.values()):
        fresh_main_urls, fresh_side_urls = get_recipe_urls(site_info)
        main_urls.extend(fresh_main_urls)
        side_urls.extend(fresh_side_urls)

    # REMOVE DUPLICATES
    print("Removing duplicate URLs")
    main_urls = list(set(main_urls))
    side_urls = list(set(side_urls))

    # REMOVE URLS ALREADY SCRAPED
    print("Removing URLs already scraped")
    main_urls = [url for url in main_urls if url not in df["canonical_url"]]
    side_urls = [url for url in side_urls if url not in df["canonical_url"]]

    # GET HTML FOR EACH RECIPE URL
    main_htmls, side_htmls = {}, {}
    print(f"Getting HTML for {len(main_urls)} main dish recipe pages")
    for url in tqdm(main_urls):
        main_htmls[url] = get_html(url)
    print(f"Getting HTML for {len(side_urls)} side dish recipe pages")
    for url in tqdm(side_urls):
        side_htmls[url] = get_html(url)

    # USE HHURSEV'S RECIPE SCRAPER
    if len(main_htmls) > 0:
        print("Scraping main course HTMLs")
        for url, html in (item for item in tqdm(main_htmls.items())):
            recipe_elements = scraper(html, url)
            if recipe_elements is not None:
                tdf = json_normalize(recipe_elements)
                tdf["used"] = [False]
                tdf["date_retrieved"] = [time.strftime("%Y-%m-%d")]
                tdf["date_sent"] = [""]
                tdf["fails"] = [False]
                print(tdf)
                print(tdf.columns)
                print(df.columns)
                df = concat([df, tdf])
                print(df.tail)
                df.reset_index(drop=True, inplace=True)
                print(df.tail)
                sys.exit()
                unused_main_recipes[url] = recipe_elements
    if len(side_htmls) > 0:
        print("Scraping side dish HTMLs")
        for url, html in (item for item in tqdm(side_htmls.items())):
            recipe_elements = scraper(html, url)
            if recipe_elements is not None:
                unused_side_recipes[url] = recipe_elements
    print(f"main {len(unused_main_recipes)}\nside {len(unused_side_recipes)}")

    return unused_main_recipes, unused_side_recipes


def get_recipe_urls(selection: dict) -> tuple[list, list]:
    """Get individual recipe URLs from website.

    Returns a tuple with URLs for entrees and side dishes.
    """
    main_html = get_html(selection["entree_page_url"])
    side_html = get_html(selection["side_page_url"])

    main_urls = re.findall(selection["regex"], main_html)
    side_urls = re.findall(selection["regex"], side_html)

    cleanup_recipe_urls(main_urls)
    cleanup_recipe_urls(side_urls)
    return main_urls, side_urls


def get_html(website: str, debug_mode=False) -> str:
    """Return HTML for a given website."""
    h = {
        "user-agent": "mozilla/5.0 (macintosh; intel mac os x \
                10_11_5) applewebkit/537.36 (khtml, like gecko) \
                chrome/50.0.2661.102 safari/537.36"
    }
    if debug_mode:
        try:
            with requests.get(website, headers=h, timeout=20) as response:
                html = response.text
        except requests.exceptions.Timeout:
            # Handle timeout gracefully
            print(f"{website} timed out. Skipping")
    else:
        try:
            with requests.get(website, headers=h, timeout=9) as response:
                html = response.text
        except requests.exceptions.Timeout:
            # Handle timeout gracefully
            print(f"{website} timed out. skipping.")
    return html


def cleanup_recipe_urls(urls: list[str]) -> None:
    """Create a list to store indices of bad entries."""
    bad_indicies = []

    for n, url in enumerate(urls):
        # Fix bad entries
        if url.lower()[:9] == "/recipes/":
            urls[n] = f"https://www.leanandgreenrecipes.net{url}"
        # Identify bad entries
        if (
            ("plan" in url.lower() or "eggplant" in url.lower())
            or (
                "dishes" in url.lower()
                and ("/recipes/" in url.lower() or "best" in url.lower())
            )
            or ("black" in url.lower() and "friday" in url.lower())
            or ("how" in url.lower() and "use" in url.lower())
            or ("dishes" in url.lower() or "ideas" in url.lower())
            or "30-whole30-meals-in-30-minutes" in url.lower()
            or "guide" in url.lower()
        ):
            # Add the index of bad entry to the list
            bad_indicies.append(n)

    # Remove bad entries in reverse order to avoid index shifting
    for i in reversed(bad_indicies):
        del urls[i]


def scraper(html: str, url: str) -> dict | None:
    """Scrape URL and returns hhursev recipe_scraper elements."""
    try:
        scrape = scrape_html(html, url)
        recipe_elements = scrape.to_json()
        # Replace returned canonical_url with the input URL if they differ
        if recipe_elements["canonical_url"] != url:
            recipe_elements["canonical_url"] = url
        # Verify recipe_elements are valid before returning
        required_keys = [
            "title",
            "site_name",
            "host",
            "ingredients",
            "instructions",
            "image",
        ]
        for key in required_keys:
            if key not in [re.lower() for re in recipe_elements]:
                raise ValueError(
                    f"Didn't find {key} in list of recipe elements. Failing. \
                    {recipe_elements['canonical_url']}"
                )

            elif recipe_elements["ingredients"] == []:
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


def get_random_proteins(recipes: dict) -> list:
    """Randomize recipe selection."""
    seafood, landfood = [], []
    for recipe in recipes.items():
        try:
            for i in recipe[1]["ingredients"]:
                i = i.lower()
                if "scallops" in i or "salmon" in i or "shrimp" in i or "tuna" in i:
                    seafood.append({recipe[0]: recipe[1]})
                elif (
                    "chickpea" in i
                    or "chicken" in i
                    or "turkey" in i
                    or "pork" in i
                    or "tofu" in i
                ):
                    landfood.append({recipe[0]: recipe[1]})
                else:
                    pass
        except TypeError:
            print(f"needs removed: {recipe}, not valid recipe")
    # shuffle the lists
    random.shuffle(landfood)
    random.shuffle(seafood)
    # select three main courses at random
    if len(landfood) > 1 and len(seafood) > 0:
        landfood = random.sample(landfood, 2)
        seafood = random.sample(seafood, 1)
    elif len(landfood) > 2 and len(seafood) == 0:
        landfood = random.sample(landfood, 3)
    else:
        print(
            "Somehow we ended up with no seafood meals and two or less "
            "landfood meals. Can't do anything with nothing. Exiting."
        )
        sys.exit()
    return landfood + seafood


def veggie_checker(meals: list, sides: dict, veggies: list) -> list:
    """Check that each main course recipe has sufficient veggies.

    If not, pull a recipe at random from the side dish list.
    """
    checked_meals = []
    for meal in meals:
        has_veggies = False
        key = next(iter(meal))
        for ingredient in meal[key]["ingredients"]:
            if any(veggie in ingredient.lower() for veggie in veggies):
                has_veggies = True
                break
        if not has_veggies:
            side = random.choice(list(sides.items()))
            side = {side[0]: side[1]}
            checked_meals.append({"type": "combo_main", "obj": meal})
            checked_meals.append({"type": "combo_side", "obj": side})
        else:
            checked_meals.append({"type": "single_main", "obj": meal})
    return checked_meals


def prettify(meals: list, start: float) -> str:
    """Convert meal object info into HTML for email.

    Receives a recipe object or dict of recipe objects.
    """
    print("Making HTML content from recipe objects.")

    # Import CSS stylesheet
    with open("style.css", "r") as f:
        css = f.read()

    html = f"{css}\t<body>\n"

    for info in meals:
        meal = info["obj"][
            next(iter(info["obj"]))
        ]  # where meal is elements of hhursev recipe-scraper object dict

        title = meal["title"]
        if info["type"] == "combo_main":
            title = f"Main: {title}"
        elif info["type"] == "combo_side":
            title = f"Side: {title}"
        title = '\t\t<div class="card">\n' f"\t\t\t<h1>{title}</h1>\n"

        try:
            servings = f'\t\t\t<i>{meal["yields"]}'
        except KeyError:
            servings = "\t\t\t<i>servings unknown"

        host = f' | {meal["site_name"]}</i>'

        title_servings = title + servings + host

        image = (
            '<div class="polaroid">\n'
            f'\t\t\t\t<img src={meal["image"]} alt="{meal["title"]} from {meal["host"]}" />\n'
            "\t\t\t</div>"
        )

        ingredients = ["\t\t\t\t<li>" + i + "</li>" for i in meal["ingredients"]]
        ingredients = "\n".join(ingredients)
        ingredients = (
            "\t\t\t<h2>Ingredients</h2>\n" f"\t\t\t<ul>\n{ingredients}\n\t\t\t</ul>"
        )

        instructions = (
            "\t\t\t<h2>Instructions</h2>\n"
            f'\t\t\t<p>{meal["instructions"]}</p>\n\t\t</div>\n'
        )

        container = "\n".join([title_servings, image, ingredients, instructions])
        html = html + container

    # some logic to handle calculating and displaying elapsed time
    elapsed_time = time.time() - start
    if elapsed_time > 1:
        elapsed_time = f"{elapsed_time:.2f} seconds"  # as time in seconds
    else:
        elapsed_time = (
            # convert from seconds to milliseconds
            f"{elapsed_time * 1000:.0f}ms"
        )

    pretty = (
        f"{html}"
        f'\t\t<p style="color: #888;text-align: center;">Wowza! We found '
        f"{len(unused_main_recipes) + len(unused_side_recipes)} recipes! \
                These {len(meals)} were "
        f"selected at random for your convenience and your family's delight. "
        f"It took {elapsed_time} to do this using v{version}."
        f"</p>\n</body>\n</html>"
    )
    return pretty


def mailer(content: str, debug_mode: bool) -> None:
    """Email pretty formatted meals to recipents, can do BCC.

    https://www.justintodata.com/send-email-using-python-tutorial/
    https://docs.python.org/3/library/email.examples.html.
    """
    # take environment variables from .env
    load_dotenv()

    msg = MIMEMultipart()
    msg["Subject"] = "Weekly Meals"
    # Set msg['Bcc'] to SENDER if in debug mode
    if debug_mode:
        msg["Bcc"] = str(os.getenv("SENDER"))
    else:
        msg["Bcc"] = str(os.getenv("BCC"))

    msg["From"] = str(os.getenv("SENDER"))
    msg.attach(MIMEText(content, "html"))

    c = ssl.create_default_context()
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=c)
    server.login(str(os.getenv("SENDER")), str(os.getenv("PASSWD")))
    # server.set_debuglevel(1)  # uncomment for more verbose terminal output
    server.send_message(msg)
    server.quit()


# START TIMER
start_time = time.time()

if __name__ == "__main__":
    websites: dict | None = load_toml(websites_filename)
    try:
        debug_mode = check_debug_mode()
        if debug_mode:
            selection = debug_list_selection()
            websites = {
                "debugging": selection
            }  # redifine websites list for debug session
            unused_main_recipes, unused_side_recipes = {}, {}
            failed_recipes, used_recipes = {}, {}

        # LOAD PREVIOUSLY COLLECTED DATA
        if not debug_mode:
            print("Loading previously collected data")
            df = load_pickle(database)

        # CHECK RECENCY OF PREVIOUSLY COLLECTED DATA
        # for this instance, files are considered old after 12 hours
        if is_file_old(database):
            print(database, "is old, getting fresh data")
            # SCRAPE FRESH DATA IF EXISTING DATA IS OLD
            df = get_fresh_data(websites, df)  # heart of the program

        df = get_fresh_data(websites, df)  # heart of the program
        sys.exit()
        # SORT BY PROTEIN AND RETURN LIST OF THREE RANDOM MEALS
        print("Getting meals with select proteins at random")
        randomized_meals = get_random_proteins(unused_main_recipes)

        # ENSURE MEALS HAVE ADEQUATE VEGGIES OR ADD A SIDE
        print("Checking for veggies")
        meals = veggie_checker(randomized_meals, unused_side_recipes, veggies)

        # PRETTYIFY THE MEALS INTO EMAILABLE HTML BODY
        print("Prettifying meals into HTML")
        pretty = prettify(meals, start_time)

        # SEND EMAIL
        print("Emailing recipients")
        mailer(pretty, debug_mode)

        if not debug_mode:
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
                    print(
                        f"{url} was not in the main or side lists,\
                            so not removing"
                    )
            print(
                f"main {len(unused_main_recipes)} final\n\
                        side {len(unused_side_recipes)} final"
            )

            # SAVE OUT DICTIONARIES AS FILES FOR REUSE
            print("Saving out files")
            save_json(unused_mains_filename, unused_main_recipes)
            save_json(unused_sides_filename, unused_side_recipes)
            save_json(failed_filename, failed_recipes)
            save_json(used_filename, used_recipes)

    except Exception as e:
        with open("error.log", "w+") as f:
            # clear existing logs
            f.write("")
            logging.exception("Code failed, see below: %s", e)
            error_content = "<br />".join(list(f.readlines()))
            mailer(error_content, True)
        raise
