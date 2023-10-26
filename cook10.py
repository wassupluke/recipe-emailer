#!/usr/bin/env python3

# TODO allow global variables where appropriate
# TODO e.g. in side_getter funcitonality

'''Import modules'''
import time
import ssl
import os
import re
from random import randrange, choice, sample
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from recipe_scrapers import scrape_me
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

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
        "https://www.wellplated.com/category/recipes-by-type/\
                entreesmain-dishes/#recent",
        "post-summary__title",
        "https://www.wellplated.com/category/recipes-by-type/\
                side-dishes-recipe-type/#recent",
    ],
    [
        "a class",
        "https://www.thespruceeats.com/dinner-4162806",
        "comp mntl-card-list-items mntl-document-card mntl-card \
                card card--no-image",
        "https://www.thespruceeats.com/side-dishes-4162722",
    ],
    [
        "a class",
        "https://nourishedbynutrition.com/recipe-index/\
                ?_sft_category=entrees",
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
        "https://www.budgetbytes.com/category/recipes/\
                ?fwp_by_course=main-dish",
        "post-summary post-summary--secondary",
        "https://www.budgetbytes.com/category/recipes/side-dish/",
    ],
    [
        "h2 class",
        "https://leanandgreenrecipes.net/recipes/category/main-course/",
        "recipe-card-title",
        "https://leanandgreenrecipes.net/recipes/category/accompaniment/",
    ],
    [
        "h3 class",
        "https://minimalistbaker.com/recipe-index/?fwp_recipe-type=entree",
        "post-summary__title",
        "https://minimalistbaker.com/recipe-index/?fwp_recipe-type=salad",
    ],
    [
        "div class",
        "https://www.gimmesomeoven.com/all-recipes/?fwp_course=main-course",
        "teaser-post-sm",
        "https://www.gimmesomeoven.com/all-recipes/?fwp_course=side-dishes",
    ]
]

# short list for debugging
debug_to_scrape = [
    [
        "div class",
        "https://www.gimmesomeoven.com/all-recipes/?fwp_course=main-course",
        "teaser-post-sm",
        "https://www.gimmesomeoven.com/all-recipes/?fwp_course=side-dishes",
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

# a list of key veggies that we want in a mea

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


def make_soup(s):
    '''Function returns BeautifulSoup object for host website'''
    h = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X \
                10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) \
                Chrome/50.0.2661.102 Safari/537.36"
    }
    response = requests.get(s, headers=h, timeout=5)
    html = response.content
    bs = BeautifulSoup(html, "html.parser")
    return bs


def scrape_by_a_class(c):
    '''Function appends links to individual recipies from host \
            website based on the target <a href> class. \
            https://www.crummy.com/software/BeautifulSoup/bs4/doc/\
            #calling-a-tag-is-like-calling-find-all'''
    recipes = soup("a", class_=c)
    for a in recipes:
        s = str(a)
        li = re.search(r'href="(\S+)"', s)
        link = li.group(1)
        if "plan" in link.lower():
            pass
        elif "30-whole30-meals-in-30-minutes" in link.lower():
            pass
        elif 'ideas' in link.lower():
            pass
        else:
            recipebook.append(link)


def scrape_by_style(y):
    '''Function appends links to individual recipies from host website\
            based on the target <a href> css-style'''
    recipes = soup("a", style=y)
    for a in recipes:
        s = str(a)
        li = re.search(r'href="(\S+)"', s)
        link = li.group(1)
        recipebook.append(link)


def scrape_by_h2(y):
    '''Function appends links to individual recipies from host website\
            based on the class of <h2> containing target <a href>'''
    recipes = soup("h2", class_=y)
    for a in recipes:
        s = str(a)
        li = re.search(r'href="(\S+)"', s)
        link = li.group(1)
        if "plan" in link.lower():
            pass
        elif link[:9] == '/recipes/':
            link = f"https://leanandgreenrecipes.net{link}"
            recipebook.append(link)
        else:
            recipebook.append(link)


def scrape_by_h3(y):
    '''Function appends links to individual recipies from host website\
            based on the class of <h3> containing target <a href>'''
    recipes = soup("h3", class_=y)
    for a in recipes:
        s = str(a)
        li = re.search(r'href="(\S+)"', s)
        link = li.group(1)
        if "plan" in link.lower():
            pass
        elif "recipes" in link.lower():
            pass
        else:
            recipebook.append(link)


def scrape_by_div(y):
    '''Function appends links to individual recipies from host website\
            based on the class of <div> containing target <a href>'''
    recipes = soup("div", class_=y)
    for a in recipes:
        s = str(a)
        li = re.search(r'href="(\S+)"', s)
        link = li.group(1)
        if "plan" in link.lower():
            pass
        elif "recipes" in link.lower():
            pass
        else:
            recipebook.append(link)


def scrape_by_parent(y):
    '''Function appends links to individual recipies from host website\
            based on the class of the parent of target <a href>'''
    recipes = soup("article", class_=y)
    for a in recipes:
        s = str(a)
        li = re.search(r'href="(\S+)"', s)
        link = li.group(1)
        if "plan" in link.lower():
            pass
        elif "recipes" in link.lower():
            pass
        else:
            recipebook.append(link)


def veggie_checker(ms, s, vl):
    '''Function checking that all meals passed in contain
    substantial vegetables'''
    print('checking that recipies have veggies')
    checked_meals = []
    sb = []
    for m in ms:
        has_veggies = False
        for i in m.ingredients():
            if any(v in i.lower() for v in vl):
                has_veggies = True
                print(f"Recipe {ms.index(m)} has veggies")
                break
        if has_veggies:
            checked_meals.append(m)
        else:
            if len(sb) != 0:
                side = sb.pop(randrange(len(sb)))
            else:
                side, sb = veggie_side_getter(s)
            print('adding a side')
            main_with_side = [m, side]
            checked_meals.append(main_with_side)
    return checked_meals, sb


def veggie_side_getter(sts):
    '''Function adds side dish to accompany main dish identified as
    lacking vegetables'''
    print('getting a links to side dishes')
    for s in sts:
        print(f'\t{s[3]}')
        if s[0] == "a class":
            scrape_by_a_class(s[2])
        elif s[0] == "a style":
            scrape_by_style(s[2])
        elif s[0] == "h2 class":
            scrape_by_h2(s[2])
        elif s[0] == "h3 class":
            scrape_by_h3(s[2])
        elif s[0] == "div class":
            scrape_by_div(s[2])
        elif s[0] == "parent class":
            scrape_by_parent(s[2])
        else:
            pass
    sb = []
    print('cooking up side meal objects')
    for r in recipebook:
        print(f'\t{r}')
        s = scrape_me(r)
        sb.append(s)
    side = sb.pop(randrange(len(sb)))
    return side, sb


def prettify(m, ar, x):
    '''Function converts meal object info into HTML for email'''
    title = m.title()
    if x == 0:
        title = f"<u>Main</u>: {title}"
    elif x == 1:
        title = f"<u>Side</u>: {title}"
    else:
        pass
    title = f"<h1 style=margin-bottom:0;>{title}</h1>"
    try:
        servings = f"<i style=margin-top:0;color:gray>{m.yields()}</i>"
    except SchemaOrgException:
        servings = "<i style=margin-top:0;color:gray>servings unknown</i>"
    title_servings = title + servings
    ingredients = ["<li>" + i + "</li>" for i in m.ingredients()]
    ingredients = "\n".join(ingredients)
    ingredients = f"<h3>Ingredients</h3>{ingredients}"
    instructions = m.instructions()
    instructions = f"<h3>Instructions</h3>\n<p>{instructions}</p>"
    r = [title_servings, ingredients, instructions]
    full_recipe = "\n\n".join(r)
    ar.append(full_recipe)
    return ar


def mailer(p):
    '''Function emails pretty formatted meals to recipents, can do BCC'''

    # https://www.justintodata.com/send-email-using-python-tutorial/
    # https://docs.python.org/3/library/email.examples.html

    load_dotenv()  # take environment variables from .env

    me = os.getenv('EMAIL_SENDER')
    msg = MIMEMultipart()
    msg['Subject'] = 'Weekly Meals'
    msg['From'] = me
    msg['Bcc'] = os.getenv('EMAIL_RECEIVER')
    msg.attach(MIMEText(p, "html"))

    context = ssl.create_default_context()
    server = smtplib.SMTP_SSL('smtp.gmail.com',
                              465, context=context)
    server.login(me, os.getenv('EMAIL_PASSWORD'))
    server.set_debuglevel(1)
    server.send_message(msg)
    server.quit()


###################################################################
###################################################################
###################################################################

if __name__ == "__main__":
    source_list = sites_to_scrape
    start = time.time()

    # Make a blank list to hold recipe links (rb for recipebook)
    recipebook = []

    print('getting initial recipe links')
    for site in source_list:
        print(f'\t{site[1]}')
        soup = make_soup(site[1])
        if site[0] == "a class":
            scrape_by_a_class(site[2])
        elif site[0] == "a style":
            scrape_by_style(site[2])
        elif site[0] == "h2 class":
            scrape_by_h2(site[2])
        elif site[0] == "h3 class":
            scrape_by_h3(site[2])
        elif site[0] == "div class":
            scrape_by_div(site[2])
        elif site[0] == "parent class":
            scrape_by_parent(site[2])
        else:
            pass

    # A blank list to hold scrape objects after they're
    # run through recipe_scrapers
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
    [meals.append(s) for s in sample(landfood_meals, 2)]
    meals.append(choice(seafood_meals))
    meals, sidebook = veggie_checker(meals, source_list, veggie_list)

    print('making HTML content from recipe objects')
    all_recipes = []
    for meal in meals:
        if not isinstance(meal, list):
            prettify(meal, all_recipes, None)
        else:
            for mea in meal:
                prettify(mea, all_recipes, meal.index(mea))
    pretty = "\n\n".join(all_recipes)
    total_sites_line = (
        f"<p style=color:gray>Wowza! We found "
        f"{len(recipebook) + len(scraperbook)} recipes! "
        f"These {len(meals)} were selected at random for "
        f"your convenience and your family's delight. "
        f"It took {(time.time() - start):.2f} seconds to do "
        f"it using v10</p>"
        )
    prettier = f"{pretty}\n\n{total_sites_line}"
    print('mailing off the list')
    print(prettier)
    print(f'# in sidebook: {len(sidebook)}')
#    mailer(pretty)
