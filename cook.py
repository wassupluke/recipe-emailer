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
from collections import defaultdict
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# IMPORT THIRD-PARTY MODULES
import requests
from dotenv import load_dotenv
from recipe_scrapers import scrape_html
from tqdm import tqdm

# IMPORT LISTS
from lists import veggies, websites

# VERSION TAG
version = 15.1


# check for debug mode or default to full mode
def check_debug_mode() -> bool:
    parser = argparse.ArgumentParser(description="Check for debug mode")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    if args.debug:
        print("Debug mode detected")
        return True
    return False


# if in debug mode, tell the user what keys (website title) are in the dictonary along with their index
def debug_list_selection() -> dict:
    print("The websites list supports the following sites:")
    websites_keys = list(WEBSITES.keys())
    for website in websites_keys:
        # note we increment by 1 to make output more user-friendly
        print(f"{websites_keys.index(website)+1}\t{website}")
    while True:
        try:
            # prompt user to enter the index of the list they wish to debug
            number = int(input("Which website would you like to debug? (#) "))
            # only accept input that would fall within the indicies of
            # the dictionary. Recall the increment
            if 1 <= number <= len(websites_keys):
                # account for the increment when saving user selection
                selection = list(WEBSITES)[number - 1]
                break
            raise ValueError
        except ValueError:
            print("I'm sorry, that wasn't a valid number.")
    # show user what they've selected before proceeding
    print(f"You've selectected to debug {selection}.")
    print("The dictionary entry is:")
    print(json.dumps(WEBSITES[selection], indent=4))
    return WEBSITES[selection]


def save_json(filename: str, data: dict) -> None:
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


# OPEN RESOURCE FILES
def load_json(filename: str) -> dict:
    try:
        with open(filename) as f:
            data = json.load(f)
        if len(data) == 0:
            raise FileNotFoundError
    except FileNotFoundError:
        print(f"Did not find {filename}, returning empty dictionary")
        return {}
    return data


def is_file_old(filename: str, old: int = 12, age: int = 12) -> bool:
    if os.path.isfile(filename):  # check that the file exists
        age = os.stat(filename).st_mtime
        age = (time.time() - age) / 3600  # convert age from seconds to hours
    return age >= old


def get_fresh_data(
    websites: dict[str, dict[str, str]],
) -> tuple[dict[str, dict], dict[str, dict]]:
    # GET LATEST URLS FROM HTML, separating entrees and sides
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
        main_htmls[url] = get_html(url)
    del main_urls
    print(f"Getting HTML for {len(side_urls)} side dish recipe pages")
    for url in tqdm(side_urls):
        side_htmls[url] = get_html(url)
    del side_urls

    # USE HHURSEV'S RECIPE SCRAPER
    if len(main_htmls) > 0:
        print("Scraping main course HTMLs")
        for url, html in (item for item in tqdm(main_htmls.items())):
            recipe_elements = scraper(html, url)
            if recipe_elements is not None:
                unused_main_recipes[url] = recipe_elements
    del main_htmls
    if len(side_htmls) > 0:
        print("Scraping side dish HTMLs")
        for url, html in (item for item in tqdm(side_htmls.items())):
            recipe_elements = scraper(html, url)
            if recipe_elements is not None:
                unused_side_recipes[url] = recipe_elements
    del side_htmls
    print(f"main {len(unused_main_recipes)}\nside {len(unused_side_recipes)}")

    return unused_main_recipes, unused_side_recipes


# getting individual recipes
# get html for both pages of each site in the dictionary (main course href and side dish href)
def get_recipe_urls(selection: dict) -> tuple[list, list]:
    main_html = get_html(selection["main course"])
    side_html = get_html(selection["side dish"])
    # using regex, match all instances of href's to individual recipes from the main course html
    main_urls = re.findall(selection["regex"], main_html)
    side_urls = re.findall(selection["regex"], side_html)
    cleanup_recipe_urls(main_urls)
    cleanup_recipe_urls(side_urls)
    return main_urls, side_urls


def get_html(website: str) -> str:
    h = {
        "user-agent": "mozilla/5.0 (macintosh; intel mac os x \
                10_11_5) applewebkit/537.36 (khtml, like gecko) \
                chrome/50.0.2661.102 safari/537.36"
    }
    if debug_mode:
        try:
            with requests.get(website, headers=h, timeout=999) as response:
                return response.text
        except requests.exceptions.Timeout:
            # Handle timeout gracefully
            print(
                f"{website} timed out after {response.elapsed.total_seconds()} seconds. Skipping"
            )
    else:
        try:
            with requests.get(website, headers=h, timeout=9) as response:
                return response.text
        except requests.exceptions.Timeout:
            # Handle timeout gracefully
            print(f"{website} timed out. skipping.")

def cleanup_recipe_urls(urls: list) -> None:
    # Fix bad entries
    for url in urls[:]:
        if url.lower().startswith("/recipes/"):
            index = urls.index(url)
            urls[index] = f"https://www.leanandgreenrecipes.net{url}"

    # Remove bad entries
    bad_keywords = [
        "plan",
        "eggplant",
        "dishes",
        "best",
        "black friday",
        "how",
        "use",
        "ideas",
        "30-whole30-meals-in-30-minutes",
        "guide",
    ]
    urls[:] = [
        url
        for url in urls
        if not any(keyword in url.lower() for keyword in bad_keywords)
    ]



def scraper(html: str, url: str) -> dict | None:
    # scrapes URL and returns hhursev recipe_scraper elements
    try:
        scrape = scrape_html(html)
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
            assert key in [i.lower() for i in recipe_elements]
            if key == "ingredients":
                assert recipe_elements[key] != []
            elif key == "instructions":
                assert recipe_elements[key] != ""
            elif key == "image":
                assert recipe_elements[key] is not None
    except AssertionError:
        failed_recipes[url] = "FAILS assertions"
        return None
    except (
        Exception
    ):  # I run this as an unattended script, so handle the error and keep going
        failed_recipes[url] = "FAILS"
        return None
    # Everything passes, return the elements
    return recipe_elements


def categorize_recipe(recipe):
    seafood_keywords = ["scallops", "salmon", "shrimp", "tuna"]
    landfood_keywords = ["chickpea", "chicken", "turkey", "pork", "tofu"]

    seafood = any(
        keyword in ingredient.lower()
        for ingredient in recipe["ingredients"]
        for keyword in seafood_keywords
    )
    landfood = any(
        keyword in ingredient.lower()
        for ingredient in recipe["ingredients"]
        for keyword in landfood_keywords
    )

    return seafood, landfood


def get_random_proteins(recipes: dict) -> list:
    seafood_recipes = []
    landfood_recipes = []

    for recipe_name, recipe in recipes.items():
        try:
            seafood, landfood = categorize_recipe(recipe)
            if seafood:
                seafood_recipes.append({recipe_name: recipe})
            elif landfood:
                landfood_recipes.append({recipe_name: recipe})
        except TypeError:
            print(f"needs removed: {recipe_name}, not valid recipe")

    if not seafood_recipes or len(landfood_recipes) < 3:
        print(
            "Somehow we ended up with no seafood meals or less than three landfood meals. Can't do anything with nothing."
        )
        return []

    random.shuffle(landfood_recipes)
    random.shuffle(seafood_recipes)

    landfood = random.sample(landfood_recipes, min(len(landfood_recipes), 3))
    seafood = random.sample(seafood_recipes, 1)

    return landfood + seafood


def veggie_checker(meals: list, sides: dict, veggies: list = None) -> dict:
    # check that each main course recipe has sufficient veggies, if not, pull a recipe at random from the side dish list
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


def prettify(meals: dict, start: float) -> str:
    """Function converts meal object info into HTML for email
    receives a recipe object or dict of recipe objects"""
    print("Making HTML content from recipe objects.")

    # Import CSS stylesheet
    with open("style.css", "r") as f:
        css = f.read()

    html = f"{css}\t<body>\n"

    for info in meals:
        # get elements of hhursev recipe-scraper object dict
        elements = info["obj"][next(iter(info["obj"]))]

        title = elements["title"]
        if info["type"] == "combo_main":
            title = f"Main: {title}"
        elif info["type"] == "combo_side":
            title = f"Side: {title}"
        title = '\t\t<div class="card">\n' f"\t\t\t<h1>{title}</h1>\n"

        try:
            servings = f'\t\t\t<i>{meal["yields"]}'
        except KeyError:
            servings = "\t\t\t<i>servings unknown"

        host = f' | {elements["site_name"]}</i>'

        title_servings = title + servings + host

        image = (
            '<div class="polaroid">\n'
            f'\t\t\t\t<img src={elements["image"]} alt="{elements["title"]} from {elements["host"]}" />\n'
            "\t\t\t</div>"
        )

        ingredients = ["\t\t\t\t<li>" + i + "</li>" for i in elements["ingredients"]]
        ingredients = "\n".join(ingredients)
        ingredients = (
            "\t\t\t<h2>Ingredients</h2>\n" f"\t\t\t<ul>\n{ingredients}\n\t\t\t</ul>"
        )

        instructions = (
            "\t\t\t<h2>Instructions</h2>\n"
            f'\t\t\t<p>{elements["instructions"]}</p>\n\t\t</div>\n'
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
        f"{len(UNUSED_MAIN_RECIPES) + len(UNUSED_SIDE_RECIPES)} recipes! These {len(meals)} were "
        f"selected at random for your convenience and your family's delight. "
        f"It took {elapsed_time} to do this using v{version}."
        f"</p>\n</body>\n</html>"
    )
    return pretty


def mailer(content: str, debug_mode: bool) -> None:
    """Function emails pretty formatted meals to recipents, can do BCC
    https://www.justintodata.com/send-email-using-python-tutorial/
    https://docs.python.org/3/library/email.examples.html"""
    # take environment variables from .env
    load_dotenv()

    msg = MIMEMultipart()
    msg["Subject"] = "Weekly Meals"
    # Set msg['Bcc'] to SENDER if in debug mode
    msg["Bcc"] = os.getenv("EMAIL_BCC")
    if debug_mode:
        msg["Bcc"] = os.getenv("EMAIL_SENDER")

    msg["From"] = os.getenv("EMAIL_SENDER")
    msg.attach(MIMEText(content, "html"))

    c = ssl.create_default_context()
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=c)
    server.login(os.getenv("EMAIL_SENDER"), os.getenv("EMAIL_PASSWORD"))
    server.send_message(msg)
    server.quit()


# START TIMER
START_TIME = time.time()

# FILENAME CONSTANTS
unused_mains_filename = "unused_mains_recipes.json"
unused_sides_filename = "unused_sides_recipes.json"
failed_filename = "failed_recipes.json"
used_filename = "used_recipes.json"

if __name__ == "__main__":
    debug_mode = check_debug_mode()
    if debug_mode:
        selection = debug_list_selection()
        websites = {"debugging": selection}  # redifine websites list for debug session
        unused_main_recipes, unused_side_recipes = {}, {}
        failed_recipes, used_recipes = {}, {}

    # LOAD PREVIOUSLY COLLECTED DATA
    if not debug_mode:
        print("Loading previously collected data")
        unused_main_recipes = load_json(unused_mains_filename)
        unused_side_recipes = load_json(unused_sides_filename)
        failed_recipes = load_json(failed_filename)
        used_recipes = load_json(used_filename)

    # CHECK RECENCY OF PREVIOUSLY COLLECTED DATA
    # for this instance, files are considered old after 12 hours
    if is_file_old(unused_mains_filename):
        print(unused_mains_filename, "is old, getting fresh data")
        # SCRAPE FRESH DATA IF EXISTING DATA IS OLD
        unused_main_recipes, unused_side_recipes = get_fresh_data(
            websites
        )  # heart of the program
        if not debug_mode:
            save_json(unused_mains_filename, unused_main_recipes)
            save_json(unused_sides_filename, unused_side_recipes)

    # SORT BY PROTEIN AND RETURN LIST OF THREE RANDOM MEALS
    print("Getting meals with select proteins at random")
    randomized_meals = get_random_proteins(UNUSED_MAIN_RECIPES)

    # ENSURE MEALS HAVE ADEQUATE VEGGIES OR ADD A SIDE
    print("Checking for veggies")
    MEALS = veggie_checker(randomized_meals, UNUSED_SIDE_RECIPES, VEGGIES)

    # PRETTYIFY THE MEALS INTO EMAILABLE HTML BODY
    print("Prettifying meals into HTML")
    PRETTY = prettify(MEALS, START_TIME)

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