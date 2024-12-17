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
version = 15.3


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
    """Save json data to a file."""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


# OPEN RESOURCE FILES
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


def is_file_old(filename: str, old: int = 12, age: int = 12) -> bool:
    """Check if a file is older than a certain age."""
    if os.path.isfile(filename):  # check that the file exists
        age = int(os.stat(filename).st_mtime)
        age = int((time.time() - age) / 3600)  # convert seconds to hours
    return age >= old


def get_fresh_data(
    websites: dict[str, dict[str, str]],
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
    print(f"Getting HTML for {len(side_urls)} side dish recipe pages")
    for url in tqdm(side_urls):
        side_htmls[url] = get_html(url)

    # USE HHURSEV'S RECIPE SCRAPER
    if len(main_htmls) > 0:
        print("Scraping main course HTMLs")
        for url, html in (item for item in tqdm(main_htmls.items())):
            recipe_elements = scraper(html, url)
            if recipe_elements is not None:
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
    main_html = get_html(selection["main course"])
    side_html = get_html(selection["side dish"])

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
            with requests.get(website, headers=h, timeout=20) as response:
                return response.text
        except requests.exceptions.Timeout:
            # Handle timeout gracefully
            print(f"{website} timed out. Skipping")
    else:
        try:
            with requests.get(website, headers=h, timeout=9) as response:
                return response.text
        except requests.exceptions.Timeout:
            # Handle timeout gracefully
            print(f"{website} timed out. skipping.")


def cleanup_recipe_urls(urls: list[str]) -> None:
    """Create a list to store indices of bad entries."""
    bad_indicies = []

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
    """Randomize recipe selection."""
    seafood, landfood = [], []
    for recipe in recipes.items():
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
START_TIME = time.time()

# FILENAME CONSTANTS
UNUSED_MAINS_FILENAME = "unused_mains_recipes.json"
UNUSED_SIDES_FILENAME = "unused_sides_recipes.json"
FAILED_FILENAME = "failed_recipes.json"
USED_FILENAME = "used_recipes.json"

if __name__ == "__main__":
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
