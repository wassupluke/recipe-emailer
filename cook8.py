from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage
from recipe_scrapers import scrape_me
from email.mime.text import MIMEText
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from random import randrange
import requests
import smtplib
import random
import time
import ssl
import os
import re

# CONSTANTS
# Info about how to process scraping recipe links each site
# sites_to_scrape format is as follows (by index):
# 0 - html attribute to locate recipies on site
# 1 - site address for main course
# 2 - html text to match for attribute 0
# 3 - site address for side dishes
sites_to_scrape = [
    [
        "a class",
        "https://www.reciperunner.com/category/recipes/dinners/",
        "wpp-post-title",
        "https://reciperunner.com/category/recipes/side-dishes/",
    ],
    [
        "a class",
        "https://www.paleorunningmomma.com/course/dinner/",
        "entry-title-link",
        "https://www.paleorunningmomma.com/course/veggies-sides/",
    ],
    [
        "h2 class",
        "https://www.skinnytaste.com/?_course=dinner-recipes",
        "entry-title",
        "https://www.skinnytaste.com/recipes/side-dishes/",
    ],
    [
        "h3 class",
        "https://www.skinnytaste.com/recipes/dinner-recipes/",
        "entry-title",
        "https://www.skinnytaste.com/recipes/side-dishes/",
    ],
    [
        "h2 class",
        "https://www.twopeasandtheirpod.com/category/recipes/main-dishes/",
        "post-summary__title",
        "https://www.twopeasandtheirpod.com/category/recipes/side/",
    ],
    [
        "h3 class",
        "https://www.wellplated.com/category/recipes-by-type/entreesmain-dishes/#recent",
        "post-summary__title",
        "https://www.wellplated.com/category/recipes-by-type/side-dishes-recipe-type/#recent",
    ],
    [
        "a class",
        "https://www.thespruceeats.com/dinner-4162806",
        "comp mntl-card-list-items mntl-document-card mntl-card card card--no-image",
        "https://www.thespruceeats.com/side-dishes-4162722",
    ],
    [
        "a class",
        "https://nourishedbynutrition.com/recipe-index/?_sft_category=entrees",
        "post",
        "https://nourishedbynutrition.com/category/recipes/sides/",
    ],
    [
        "h2 class",
        "https://www.eatingbirdfood.com/category/meal-type/dinnerlunch/",
        "post-summary__title",
        "https://www.eatingbirdfood.com/category/meal-type/dinnerlunch/sides/",
    ],
    [
        "parent class",
        "https://www.budgetbytes.com/category/recipes/?fwp_by_course=main-dish",
        "post-summary post-summary--secondary",
        "https://www.budgetbytes.com/category/recipes/side-dish/",
    ],
]

# short list for debugging
debug_to_scrape = [
    [
        "parent class",
        "https://www.budgetbytes.com/category/recipes/?fwp_by_course=main-dish",
        "post-summary post-summary--secondary",
        "https://www.budgetbytes.com/category/recipes/side-dish/",
    ]
]

# Not yet usable on recipe_scrapers
wild_sites = [
    [
        "a style",
        "https://www.dishingouthealth.com/category/recipes/dinner/",
        "text-decoration: none;",
    ]
]

# a list of key veggies that we want in a meal
veggie_list = [
    "acorn aquash",
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


def make_soup(site):
    h = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
    }
    response = requests.get(site, headers=h)
    html = response.content
    soup = BeautifulSoup(html, "html.parser")
    return soup


def scrape_by_a_class(soup, c, rb):
    recipes = soup("a", class_=c)
    for a in recipes:
        s = str(a)
        title = a.text
        li = re.search(r'href="(\S+)"', s)
        link = li.group(1)
        if "plan" in link.lower():
            pass
        elif "30-whole30-meals-in-30-minutes" in link.lower():
            pass
        elif 'ideas' in link.lower():
            pass
        else:
            rb.append(link)
    return rb


def scrape_by_style(soup, y, rb):
    recipes = soup("a", style=y)
    for a in recipes:
        s = str(a)
        title = a.text
        li = re.search(r'href="(\S+)"', s)
        link = li.group(1)
        rb.append(link)
    return rb


def scrape_by_h2(soup, y, rb):
    recipes = soup("h2", class_=y)
    for a in recipes:
        s = str(a)
        title = a.text
        li = re.search(r'href="(\S+)"', s)
        link = li.group(1)
        if "plan" in link.lower():
            pass
        else:
            rb.append(link)
    return rb


def scrape_by_h3(soup, y, rb):
    recipes = soup("h3", class_=y)
    for a in recipes:
        s = str(a)
        title = a.text
        li = re.search(r'href="(\S+)"', s)
        link = li.group(1)
        if "plan" in link.lower():
            pass
        elif "recipes" in link.lower():
            pass
        else:
            rb.append(link)
    return rb


def scrape_by_parent(soup, y, rb):
    recipes = soup("article", class_=y)
    for a in recipes:
        s = str(a)
        title = a.text
        li = re.search(r'href="(\S+)"', s)
        link = li.group(1)
        if "plan" in link.lower():
            pass
        elif "recipes" in link.lower():
            pass
        else:
            rb.append(link)
    return rb


def veggie_checker(meals, sites_to_scrape, veggie_list):
    print('checking that recipies have veggies')
    checked_meals = []

    for meal in meals:
        has_veggies = False
        for ingredient in meal.ingredients():
            if any(veggie in ingredient.lower() for veggie in veggie_list):
                has_veggies = True
                break
            else:
                pass

        if has_veggies:
            checked_meals.append(meal)
        else:
            print('adding a side')
            try:
                side = sidebook.pop(randrange(len(sidebook)))
            except NameError:
                side, sidebook = veggie_side_getter(sites_to_scrape)
            main_with_side = [meal, side]
            checked_meals.append(main_with_side)

    return checked_meals


def veggie_side_getter(sites_to_scrape):
    print('getting a links to side dishes')
    recipebook = []
    for site in sites_to_scrape:
        print(f'\t{site[3]}')
        soup = make_soup(site[3])
        if site[0] == "a class":
            scrape_by_a_class(soup, site[2], recipebook)
        elif site[0] == "a style":
            scrape_by_style(soup, site[2], recipebook)
        elif site[0] == "h2 class":
            scrape_by_h2(soup, site[2], recipebook)
        elif site[0] == "h3 class":
            scrape_by_h3(soup, site[2], recipebook)
        elif site[0] == "parent class":
            scrape_by_parent(soup, site[2], recipebook)
        else:
            pass
    sidebook = []
    print(f'cooking up side meal objects')
    for site in recipebook:
        print(f'\t{site}')
        scraper = scrape_me(site)
        sidebook.append(scraper)
    side = sidebook.pop(randrange(len(sidebook)))
    return side, sidebook


def prettify(meal, all_recipes, x):
    title = meal.title()
    if x == 0:
        title = "<u>Main</u>: {}".format(title)
    elif x == 1:
        title = "<u>Side</u>: {}".format(title)
    else:
        pass
    Title = f"<h1 style=margin-bottom:0;>{title}</h1>"
    try:
        Servings = f"<i style=margin-top:0;color:gray>{meal.yields()}</i>"
    except SchemaOrgException:
        Servings = f"<i style=margin-top:0;color:gray>servings unknown</i>"
    Title_Servings = Title + Servings
    ingredients = ["<li>" + i + "</li>" for i in meal.ingredients()]
    Ingredients = "\n".join(ingredients)
    Ingredients = f"<h3>Ingredients</h3>{Ingredients}"
    instructions = meal.instructions()
    Instructions = f"<h3>Instructions</h3>\n<p>{instructions}</p>"
    recipe = [Title_Servings, Ingredients, Instructions]
    full_recipe = "\n\n".join(recipe)
    all_recipes.append(full_recipe)
    return all_recipes


def mailer(pretty):  # https://www.justintodata.com/send-email-using-python-tutorial/
    # https://docs.python.org/3/library/email.examples.html

    load_dotenv()  # take environment variables from .env

    me = os.getenv('EMAIL_SENDER')
    msg = MIMEMultipart()
    msg['Subject'] = 'Weekly Meals'
    msg['From'] = me
    msg['Bcc'] = os.getenv('EMAIL_BCC')
    msg.attach(MIMEText(pretty, "html"))

    context = ssl.create_default_context()
    server = smtplib.SMTP_SSL('smtp.gmail.com',465,context=context)
    server.login(me,os.getenv('EMAIL_PASSWORD'))
    server.set_debuglevel(1)
    server.send_message(msg)
    server.quit()

###################################################################
###################################################################
###################################################################

if __name__ == "__main__":
    source_list = sites_to_scrape
    start = time.time()

    # Make a blank list to hold links to recipes (rb for recipebook)
    recipebook = []

    print('getting initial recipe links')
    for site in source_list:
        print(f'\t{site[1]}')
        soup = make_soup(site[1])
        if site[0] == "a class":
            scrape_by_a_class(soup, site[2], recipebook)
        elif site[0] == "a style":
            scrape_by_style(soup, site[2], recipebook)
        elif site[0] == "h2 class":
            scrape_by_h2(soup, site[2], recipebook)
        elif site[0] == "h3 class":
            scrape_by_h3(soup, site[2], recipebook)
        elif site[0] == "parent class":
            scrape_by_parent(soup, site[2], recipebook)
        else:
            pass

    # A blank list to hold scrape objects after they're run through recipe_scrapers
    scraperbook = []

    # Lists to hold sorted recipes
    seafood_meals = []
    landfood_meals = []

    print('cooking up recipe objects')
    for recipe in recipebook:
        print(f'\t{recipe}')
        scraper = scrape_me(recipe)
        scraperbook.append(scraper)
        for ingredient in scraper.ingredients():
            if "salmon" in ingredient.lower():
                seafood_meals.append(scraper)
            elif "shrimp" in ingredient.lower():
                seafood_meals.append(scraper)
            elif "chicken" in ingredient.lower():
                landfood_meals.append(scraper)
            elif "pork" in ingredient.lower():
                landfood_meals.append(scraper)
            elif "turkey" in ingredient.lower():
                landfood_meals.append(scraper)
            else:
                pass

    meals = []
    meals.append(landfood_meals.pop(randrange(len(landfood_meals))))
    meals.append(landfood_meals[randrange(len(landfood_meals))])
    if len(seafood_meals) > 0:
        meals.append(seafood_meals[randrange(len(seafood_meals))])
    else:
        meals.append(landfood_meals.pop(randrange(len(landfood_meals))))
    meals = veggie_checker(meals, source_list, veggie_list)

    print('making HTML content from recipe objects')
    all_recipes = []
    for meal in meals:
        if type(meal) is not list:
            prettify(meal, all_recipes, None)
        else:
            for m in meal:
                prettify(m, all_recipes, meal.index(m))

    pretty = "\n\n".join(all_recipes)
    total_sites_line = f"<p style=color:gray>Wowza! We found {len(recipebook)} recipes! These {len(meals)} were selected at random for your convenience and your family's delight.</p>"
    pretty = f"{pretty}\n\n{total_sites_line}"
    print('mailing off the list')
    mailer(pretty)

    """
    dishingouthealth :: NOT ON RECIPE_SCRAPER
    slimmingeats  :: NOT ON RECIPE_SCRAPER
    cleanfoodcrush :: NOT ON RECIPE_SCRAPER
    thereciperebel :: NOT ON RECIPE_SCRAPER
    saltandlavender :: NOT ON RECIPE_SCRAPER
    wowstaceyhawkins :: NOT ON RECIPE_SCRAPER
    """
