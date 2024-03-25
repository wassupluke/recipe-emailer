#!/usr/bin/env python3

import pprint
import json
import pickle
import random
import re
import requests
import sys
import os
import time
from lists2 import websites, veggies
from recipe_scrapers import scrape_me
from tqdm import tqdm

# check for debug mode or default to full mode
def check_debug_mode() -> bool:
    if len(sys.argv) != 1:
        if sys.argv[1] == "-d" or sys.argv[1] == "--debug":
            print("debug mode detected")
            return True
    return False


# if in debug mode, tell the user what keys (website title) are in the dictonary along with their index
def debug_list_selection() -> dict:
    print("The websites list supports the following sites:")
    for website in websites.keys():
        print(f"{list(websites.keys()).index(website)+1}\t{website}")
    while True:
        try:
# prompt user to enter the index of the list they wish to debug
            number = int(input("Which website would you like to debug? (#) "))
# only accept input that would fall within the indicies of the dictionary
            if number > 0 and number < len(websites.keys()) + 1:
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


# OPENING RESOURCE FILES
def save_json(filename: str, data: dict) -> None:
    with open(filename+".json", "w") as f:
        json.dump(data, f)


def load_json(filename: str) -> dict:
    try:
        with open(filename+".json") as f:
            data = json.load(f)
        if len(data) == 0:
            raise FileNotFoundError
    except FileNotFoundError:
        print(f'Did not find {filename}.json, returning empty dictionary')
        return dict()
    return data


# getting individual recipes
# get html for both pages of each site in the dictionary (main course href and side dish href)
def get_recipe_urls(selection: dict) -> list:
# using regex, match all instances of href's to individual recipes from the main course html
    main_html = get_html(selection['main course'])
    side_html = get_html(selection['side dish'])
    main_urls = re.findall(selection['regex'], main_html)
    side_urls = re.findall(selection['regex'], side_html)
    main_urls = cleanup_recipe_urls(main_urls)
    side_urls = cleanup_recipe_urls(side_urls)
    return main_urls, side_urls


def get_html(website: str) -> str:
    h = {
        "user-agent": "mozilla/5.0 (macintosh; intel mac os x \
                10_11_5) applewebkit/537.36 (khtml, like gecko) \
                chrome/50.0.2661.102 safari/537.36"
    }
    try:
        response = requests.get(website, headers=h, timeout=5)
    except requests.exceptions.timeout:
        print(f'{website} timed out. skipping.')
    return response.text


def cleanup_recipe_urls(urls: list) -> list:
    for url in urls:
        # fix bad entries
        if url.lower()[:9] == '/recipes/':
            index = urls.index(url)
            urls[index] = f'https://www.leanandgreenrecipes.net{url}'
        # remove bad entries
        if (
            ('plan' in url.lower() or 'eggplant' in url.lower())
            or ('dishes' in url.lower() \
                and ('/recipes/' in url.lower() or 'best' in url.lower()))
            or ('black' in url.lower() and 'friday' in url.lower())
            or ('how' in url.lower() and 'use' in url.lower())
            or ('dishes' in url.lower() or 'ideas' in url.lower())
            or '30-whole30-meals-in-30-minutes' in url.lower()
            or 'guide' in url.lower()
        ):
            urls.remove(url)
    return urls


def scraper(url: str) -> dict:
	scrape = scrape_me(url)
	try:
		recipe_elements = scrape.to_json()
		if recipe_elements['canonical_url'] != url:
			recipe_elements['canonical_url'] = url
	except exception as e:
		print(e)
		return
	return recipe_elements


def get_random_main_courses(recipes: dict) -> dict:
    ...


def get_random_side_dish(sides: dict) -> dict:
    ...


def get_random_proteins(recipes: dict) -> list:
    seafood, landfood = list(), list()
    for recipe in recipes.items():
        try:
            for i in recipe[1]['ingredients']:
                i = i.lower()
                if (
                        'scallops' in i
                        or 'salmon' in i
                        or 'shrimp' in i
                        or 'tuna' in i
                ):
                    seafood.append({recipe[0] : recipe[1]})
                elif (
                        'chickpea' in i
                        or 'chicken' in i
                        or 'turkey' in i
                        or 'pork' in i
                        or 'tofu' in i
                ):
                    landfood.append({recipe[0] : recipe[1]})
                else:
                    pass
        except TypeError:
            print(f'needs removed: {recipe}, not valid recipe')
    # shuffle the lists
    random.shuffle(landfood)
    random.shuffle(seafood)
    if len(landfood) > 1 and len(seafood) > 0:
        landfood = random.sample(landfood, 2)
        seafood = random.sample(seafood, 1)
    elif len(landfood) > 2 and len(seafood) == 0:
        landfood = random.sample(landfood, 3)
    else:
        print('Somehow we ended up with no seafood meals and two or less '
            'landfood meals. Can\'t do anything with nothing. Exiting.')
        sys.exit()
    return landfood + seafood


def veggie_checker(meals: list, sides: dict, veggies: list = veggies):
    checked_meals = list()
    for meal in meals:
        has_veggies = False
        key = next(iter(meal))
        for ingredient in meal[key]['ingredients']:
            if any(veggie in ingredient.lower() for veggie in veggies):
                has_veggies = True
                break
        if not has_veggies:
            side = random.choice(list(sides.items()))
            side = {side[0] : side[1]}
            checked_meals.append({'type' : 'main', 'obj' : meal})
            checked_meals.append({'type' : 'side', 'obj' : side})
        else:
            checked_meals.append({'type' : 'main', 'obj' : meal})
    return checked_meals


# if not in debug mode, remove hrefs already present in used-recipes and unused-recipes as we already have objects for these
# using regex, match all instances of href's to individual recipes from the side dish html
# if not in debug mode, remove hrefs already present in used-recipes and unused-recipes as we already have objects for these

# scraping individual recipes
# using hhursev's recipe scraper, scrape each individual recipe from the remaining urls in the main course list
# using hhursev's recipe scraper, scrape each individual recipe from the remaining urls in the side dish list

# randomizing recipe selection
# select three main courses at random
# check that each main course recipe has sufficient veggies, if not, pull a recipe at random from the side dish list

# prettifying and emailing
# open the html template file
# prettify the recipe objects into emailable html body and insert into the template
# email the final product

# updating resource pickles
# update the used-recipes and unused-recipes reference files and pickel them back up for next time


# filename constants
unused_mains_filename = "unused_mains_recipes"
unused_sides_filename = "unused_sides_recipes"
used_filename = "used_recipes"

debug_mode = check_debug_mode()
if debug_mode:
    selection = debug_list_selection()
    websites = {'debugging': selection}
    unused_main_recipes, unused_side_recipes, scraped_mains, scraped_sides = {}, {}, {}, {}
    unused_main_recipes = load_json(unused_mains_filename)
    print(unused_main_recipes)

else:
    # LOAD PREVIOUSLY COLLECTED DATA
    print('loading previously collected data')
    unused_main_recipes = load_json(unused_mains_filename)
    unused_side_recipes = load_json(unused_sides_filename)
    used_recipes = load_json(used_filename)

    # CHECK FILE AGE AND SKIP GETTING HTML IF IT'S FRESH
    age = os.stat(unused_mains_filename + '.json').st_mtime
    age = (time.time() - age) / 3600
    if age > 12:
        # GET LATEST URLS FROM HTML, separating entrees and sides
        main_urls, side_urls = list(), list()
        print('getting html')
        for site_info in tqdm(websites.values()):
            fresh_main_urls, fresh_side_urls = get_recipe_urls(site_info)
            main_urls.extend(fresh_main_urls)
            side_urls.extend(fresh_side_urls)

        # REMOVE DUPLICATES
        print('removing duplicate urls')
        main_urls = list(set(main_urls))
        side_urls = list(set(side_urls))


        # REMOVE URLS ALREADY SCRAPED
        print('removing urls already scraped')
        main_urls = [url for url in main_urls if url not in unused_main_recipes.keys()]
        side_urls = [url for url in side_urls if url not in unused_side_recipes.keys()]

        # REMOVE URLS ALREADY SENT
        print('removing urls already sent')
        main_urls = [url for url in main_urls if url not in used_recipes.keys()]
        side_urls = [url for url in side_urls if url not in used_recipes.keys()]
        print(f"main {len(main_urls)} new\nside {len(side_urls)} new")

        # USE HHURSEV'S RECIPE SCRAPER
        print('scraping main course urls')
        for url in tqdm(main_urls):
            unused_main_recipes[url] = scraper(url)
        print('scraping side dish urls')
        for url in tqdm(side_urls):
            unused_side_recipes[url] = scraper(url)
        print(f"main {len(unused_main_recipes)}\nside {len(unused_side_recipes)}")

    # SORT BY PROTEIN AND RETURN LIST OF THREE RANDOM MEALS
    print('getting meals with select proteins at random')
    randomized_meals = get_random_proteins(unused_main_recipes)

    # ENSURE MEALS HAVE ADEQUATE VEGGIES OR ADD A SIDE
    print('checking for veggies')
    meals = veggie_checker(randomized_meals, unused_side_recipes)
    for meal in meals:
        for value in meal['obj'].values():
            print(meal['type'] + " : " + value['title'])
    print(len(meals))
    sys.exit()

    # SAVE OUT DICTIONARIES AS FILES FOR REUSE
    print('saving out files')
    save_json(unused_mains_filename, unused_main_recipes)
    save_json(unused_sides_filename, unused_side_recipes)
