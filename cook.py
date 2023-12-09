#!/usr/bin/env python3

# Standard Library Imports
import json
import logging
import os
import re
import smtplib
import ssl
import time
from random import choice, randrange, sample, shuffle, randint
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Third-Party Libraries
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from recipe_scrapers import scrape_me

# Local Imports
from css import head
from lists import full, debug, veggie_list


def get_links(sl: list[str], rb: list, index: int=2) -> list[str]:
    """Function returns BeautifulSoup object for host website"""
    print(f"Getting HTML from {sl[index]}")
    h = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X \
                10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) \
                Chrome/50.0.2661.102 Safari/537.36"
    }
    try:
        response = requests.get(sl[index], headers=h, timeout=5)
    except requests.exceptions.Timeout:
        print(f"{sl[index]} timed out. Skipping.")
    html = response.content
    soup = BeautifulSoup(html, "html.parser")
    if sl[0].split(" ")[1] == "class":
        r = soup(sl[0].split(" ")[0], class_=sl[1])
    elif sl[0].split(" ")[1] == "a style":
        r = soup(sl[0].split(" ")[0], style=sl[1])
    links = [re.search(r'href="(\S+)"', str(a)).group(1) for a in r]
    clean_links = []
    for i in links:
        if i.lower()[:9] == "/recipes/":
            clean_links.append(f"https://www.leanandgreenrecipes.net{i}")
        elif (
            i not in recipebook
            or ("plan" not in i.lower() or 'eggplant' in i.lower())
            or ("dishes" not in i.lower() \
                and ("/recipes/" in i.lower() or 'best' not in i.lower()))
            or ('black' not in i.lower() and 'friday' not in i.lower())
            or ('how' not in i.lower() and 'use' not in i.lower())
            or ("dishes" not in i.lower() or 'ideas' not in i.lower())
            or "30-whole30-meals-in-30-minutes" not in i.lower()
        ):
            clean_links.append(i)
        else:
            pass
    return clean_links


def scrape(
    u: str,
    landfood_meals: list[str],
    seafood_meals: list[str],
    other_meals: list[str]
    ) -> None:
    """Function uses @hhursev's recipe_scrapers python package to get all
    recipe info and returns an object"""
    print(f"\t scraping {u}")
    scraper = scrape_me(u)
    try:
        print(f'\t\t{scraper.title()}')
        for i in scraper.ingredients():
            i = i.lower()
            if "salmon" in i or "shrimp" in i \
               or "scallops" in i or "tuna" in i:
                seafood_meals.append(scraper)
            elif "chicken" in i or "pork" in i or "turkey" in i:
                landfood_meals.append(scraper)
            else:
                pass
    except TypeError:
        print(f'Needs removed: {u}, not valid recipe')


def randomize_proteins(
    meals: list[str],
    landfood_meals: list[str],
    seafood_meals: list[str]
    ) -> list[str]:
    """Function takes all meals and picks one seafood meal and two landfood
    meals at random"""
    print("Picking three protein meals at random.")
    print(
        f"{len(seafood_meals)} seafood meals\n"
        f"{len(landfood_meals)} landfood meals"
    )
    # shuffle the lists
    shuffle(seafood_meals)
    shuffle(landfood_meals)
    if len(seafood_meals) > 0 and len(landfood_meals) > 1:
        meals.append(choice(seafood_meals))
        [meals.append(s) for s in sample(landfood_meals, 2)]
    elif len(seafood_meals) == 0 and len(landfood_meals) > 2:
        [meals.append(s) for s in sample(landfood_meals, 3)]
    else:
        print(
            "Somehow we ended up with no seafood meals and two or "
            "less landfood meals"
        )
        raise EOFError
    return meals


def veggie_checker(
    ms: list[str],
    vl: list[str],
    sl: list[list[str]],
    rb: list[str]
    ) -> list[list[str], list[str]]:
    """Function checking that all meals passed in contain
    substantial vegetables"""
    print("Checking that recipies have veggies.")
    checked_meals = []
    sb = []
    for m in ms:
        has_veggies = False
        for i in m.ingredients():
            if any(v in i.lower() for v in vl):
                has_veggies = True
                print(f"\trecipe {ms.index(m)}, {m.title()}, has veggies")
                break
        if has_veggies:
            checked_meals.append({"type": "whole", "obj": m})
        else:
            if len(sb) == 0:
                print(f'\trecipe {ms.index(m)}, {m.title()}, NEEDS veggies')
                lists = [get_links(s, rb, 3) for s in sl]
                sb = list(set(item for s in lists for item in s))
            side = scrape_me(sb.pop(randrange(len(sb))))
            checked_meals.append({"type": "main", "obj": m})
            checked_meals.append({"type": "side", "obj": side})
    return checked_meals, sb


def prettify(
    meals: list[str],
    used: list[str],
    unused: list[str],
    head: str,
    start: float,
    rb: list[list[str]],
    sb: list[str]
    ) -> list[str, list[str], list[str]]:
    """Function converts meal object info into HTML for email
    receives a recipe object or dict of recipe objects"""
    print("Making HTML content from recipe objects.")

    html = f"{head}\n<body>\n"

    for i in meals:
        m = i.get("obj")

        # update used list
        used.append(m.canonical_url())

        title = m.title()
        if i.get("type") == "main":
            title = f"Main: {title}"
        elif i.get("type") == "side":
            title = f"Side: {title}"
        title = f"<section>\n<h1>{title}</h1>\n"

        try:
            servings = f"<i>{m.yields()}</i>"
        except:
            servings = "<i>servings unknown</i>"
        title_servings = title + servings

        ingredients = ["<li>" + i + "</li>" for i in m.ingredients()]
        ingredients = "\n".join(ingredients)
        ingredients = (
            f'<div class="row">\n'
            f'<div class="column">\n<h3>Ingredients</h3>\n'
            f'<ul>\n{ingredients}\n</ul>\n</div>'
        )

        image = (
            f'<div class="column">\n<div class="polaroid">\n'
            f'<a style="rotate:{randint(-10,10)}deg">\n'
            f'<img src={m.image()} alt="{m.title()} from {m.host()}" />\n'
            f'</a>\n</div>\n</div>\n</div>'
        )

        instructions = (
                f'<span style="display: block;"><h3>Instructions</h3>\n'
            f'<p>{m.instructions()}</p>\n</span>\n</section>\n\n'
        )

        section = "\n".join([title_servings, ingredients, image, instructions])
        html = html + section

    pretty = (
        f'{html}\n'
        f'<p style="color: #888;text-align: center;">Wowza! We found '
        f"{len(recipebook) + len(sidebook)} recipes! These {len(meals)} were "
        f"selected at random for your convenience and your family's delight. "
        f"It took {(time.time() - start):.2f} seconds to do this using v11."
        f"</p>\n</body>\n</html>"
    )

    # update unused list
    unused = [u for u in unused if u not in used]
    print(pretty)
    print(f"{len(unused)} unused recipes.\n{len(used)} used recipes.")
    return pretty, used, unused


def mailer(p: str, s: list[list[str]]) -> None:
    """Function emails pretty formatted meals to recipents, can do BCC
    https://www.justintodata.com/send-email-using-python-tutorial/
    https://docs.python.org/3/library/email.examples.html"""
    # take environment variables from .env
    load_dotenv()

    msg = MIMEMultipart()
    msg["Subject"] = "Weekly Meals"
    msg["From"] = os.getenv("EMAIL_SENDER")
    msg["Bcc"] = os.getenv("EMAIL_BCC")
    msg.attach(MIMEText(p, "html"))

    c = ssl.create_default_context()
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=c)
    server.login(os.getenv("EMAIL_SENDER"), os.getenv("EMAIL_PASSWORD"))
    server.set_debuglevel(1)
    server.send_message(msg)
    server.quit()


# -----------------------------------------------------------------#

if __name__ == "__main__":
    # Initilize logging
    logging.basicConfig(filename="error.log", level=logging.DEBUG)

    # Initialize lists
    landfood_meals, seafood_meals, other_meals, meals = [], [], [], []

    try:
        # source_list can take either full or debug
        source_list = full

        # start timing the whole process
        start = time.time()

        # load or create unused recipe file
        try:
            with open("unused_recipes.json") as f:
                recipebook = json.load(f)
        except FileNotFoundError:
            recipebook = []
            with open("unused_recipes.json", "a") as f:
                json.dump([], f)

        # load or create used recipe file
        try:
            with open("used_recipes.json") as f:
                used = json.load(f)
        except FileNotFoundError:
            used = []
            with open("used_recipes.json", "a") as f:
                json.dump([], f)

        # gets all recipes from each site in source_list
        lists = [get_links(s, recipebook) for s in source_list]

        # remove nested lists and duplicate links
        recipebook = list(set(item for s in lists for item in s))

        # meals that haven't been sent
        unused = {r for r in recipebook if r not in used}

        # get recipe_scrapers object for each recipe
        print("Cooking up recipe objects using @hhursev's recipe_scrapers.")
        [scrape(u, landfood_meals, seafood_meals, other_meals) for u in unused]

        # sort by protein and return list of three random meals
        randomized_meals = randomize_proteins(
            meals,
            landfood_meals,
            seafood_meals
            )

        # ensure each meal has at least one veggie from veggie_list
        checked_meals, sidebook = veggie_checker(
            randomized_meals,
            veggie_list,
            source_list,
            recipebook
            )

        # prettify recipes with HTML
        pretty, used, unused = prettify(
            checked_meals,
            used,
            unused,
            head,
            start,
            recipebook,
            sidebook
            )

        # save unused recipes to file
        with open('unused_recipes.json', 'w') as f:
            json.dump(unused, f)

        # save sent recipes to file
        with open('used_recipes.json', 'w') as f:
            json.dump(used, f)

        # email the prettiest HTML to msg['Bcc']
        print('trying to email the list')
        mailer(pretty, source_list)

    except Exception as e:
        with open("error.log", "w+") as f:
            # clear existing logs
            f.write("")
        logging.exception("Code failed, see below: %s", e)
        raise
