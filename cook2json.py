#!/usr/bin/env python3

# TODO allow global variables where appropriate
# TODO e.g. in side_getter funcitonality

'''Import modules'''
import time
import re
from datetime import date
from recipe_scrapers import scrape_me
from random import sample
import json
import requests
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
        if link in recipebook \
           or "plan" in link.lower() \
           or "30-whole30-meals-in-30-minutes" in link.lower() \
           or 'ideas' in link.lower():
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
        if link in recipebook:
            pass
        recipebook.append(link)


def scrape_by_h2(y):
    '''Function appends links to individual recipies from host website\
            based on the class of <h2> containing target <a href>'''
    recipes = soup("h2", class_=y)
    for a in recipes:
        s = str(a)
        li = re.search(r'href="(\S+)"', s)
        link = li.group(1)
        if link in recipebook \
           or "plan" in link.lower():
            pass
        elif link[:9] == '/recipes/':
            recipebook.append(f"https://leanandgreenrecipes.net{link}")
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
        if link in recipebook \
           or "plan" in link.lower() \
           or "recipes" in link.lower():
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
        if link in recipebook \
           or "plan" in link.lower() \
           or "recipes" in link.lower():
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
        if link in recipebook \
           or "plan" in link.lower() \
           or "recipes" in link.lower():
            pass
        else:
            recipebook.append(link)


###################################################################
###################################################################
###################################################################

if __name__ == "__main__":
    source_list = sites_to_scrape

# load or create unused recipe list
    try:
        with open('unused_recipes.json') as f:
            recipebook = json.load(f)
    except FileNotFoundError:
        recipebook = []
        with open('unused_recipes.json', 'a') as f:
            json.dump([],f)

# load or create used recipe list
    try:
        with open('used_recipes.json') as f:
            used = json.load(f)
    except FileNotFoundError:
        used = []
        with open('used_recipes.json', 'a') as f:
            json.dump([],f)

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

print(f'len {len(recipebook)} items')
recipebook = list(set(recipebook))  # remove duplicates
print(f'after set len {len(recipebook)} items')

# meals that haven't been sent
unused = [r for r in recipebook if r not in used]
print(f'unused {len(unused)} items')

meals = []
[meals.append(s) for s in sample(unused, 3)]

# save unused recipes to file
with open('unused_recipes.json', 'w') as f:
    json.dump(unused, f)

# save sent recipes to file
with open('used_recipes.json', 'w') as f:
    used.extend(meals)
    json.dump(used, f)  
