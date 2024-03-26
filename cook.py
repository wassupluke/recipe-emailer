#!/usr/bin/env python3

import json
import random
import re
import requests
import smtplib
import ssl
import sys
import os
import time
from lists import websites, veggies
from recipe_scrapers import scrape_me
from tqdm import tqdm
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


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
    with open(filename, "w") as f:
        json.dump(data, f)


def load_json(filename: str) -> dict:
    try:
        with open(filename) as f:
            data = json.load(f)
        if len(data) == 0:
            raise FileNotFoundError
    except FileNotFoundError:
        print(f'Did not find {filename}, returning empty dictionary')
        return dict()
    return data


def is_file_old(filename: str, age: int) -> bool:
    if os.path.isfile(filename):  # check that the file exists
        age = os.stat(filename).st_mtime
        age = (time.time() - age) / 3600  # convert age from seconds to hours
    if age < 12:
        return False
    return True


def get_fresh_data(websites: dict):
    # GET LATEST URLS FROM HTML, separating entrees and sides
    main_urls, side_urls = list(), list()
    print('Getting HTML')
    for site_info in tqdm(websites.values()):
        fresh_main_urls, fresh_side_urls = get_recipe_urls(site_info)
        main_urls.extend(fresh_main_urls)
        side_urls.extend(fresh_side_urls)

    # REMOVE DUPLICATES
    print('Removing duplicate urls')
    main_urls = list(set(main_urls))
    side_urls = list(set(side_urls))


    # REMOVE URLS ALREADY SCRAPED
    print('Removing urls already scraped')
    main_urls = [url for url in main_urls if url not in unused_main_recipes.keys()]
    side_urls = [url for url in side_urls if url not in unused_side_recipes.keys()]

    # REMOVE URLS ALREADY SENT
    print('Removing urls already sent')
    main_urls = [url for url in main_urls if url not in used_recipes.keys()]
    side_urls = [url for url in side_urls if url not in used_recipes.keys()]
    print(f"main {len(main_urls)} new\nside {len(side_urls)} new")

    # USE HHURSEV'S RECIPE SCRAPER
    print('Scraping main course urls')
    for url in tqdm(main_urls):
        unused_main_recipes[url] = scraper(url)
    del main_urls
    print('Scraping side dish urls')
    for url in tqdm(side_urls):
        unused_side_recipes[url] = scraper(url)
    del side_urls
    print(f"main {len(unused_main_recipes)}\nside {len(unused_side_recipes)}")
    return unused_main_recipes, unused_side_recipes
    

# getting individual recipes
# get html for both pages of each site in the dictionary (main course href and side dish href)
def get_recipe_urls(selection: dict) -> list:
    main_html = get_html(selection['main course'])
    side_html = get_html(selection['side dish'])
    # using regex, match all instances of href's to individual recipes from the main course html
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


def scraper(url: str) -> dict:  # scrapes URL and returns hhursev recipe_scraper elements
    scrape = scrape_me(url)
    try:
        recipe_elements = scrape.to_json()
        # replace returned canonical_url with the URL used as input for the scraper if the two differ
        if recipe_elements['canonical_url'] != url:
            recipe_elements['canonical_url'] = url

        # check that the elements used by this script are valid
        assert recipe_elements['title'].isalnum() is True
        assert recipe_elements['yields'].isalnum() is True
        assert recipe_elements['site_name'].isalnum() is True
        assert recipe_elements['host'].isalnum() is True
        assert recipe_elements['ingredients'] != []
        assert recipe_elements['instructions'] != ''
        assert recipe_elements['image'] is not None
    except exception as e:
        print(e)
        return
    return recipe_elements


def clean_dictionary(meals):
    print(len(meals))
    required_fields = ['title', 'yields', 'site_name', 'host', 'ingredients', 'instructions', 'image']
    remove_us = list()
    
    for pair in meals.items():
        key = pair[0]
        recipe_elements = pair[1]
        if all(req in recipe_elements for req in required_fields):
            try:
                assert recipe_elements['ingredients'] != []
                assert recipe_elements['instructions'] != ''
                assert recipe_elements['image'] is not None
            except AssertionError:
                remove_us.append(key)
        else:
            remove_us.append(key)

    for key in remove_us:
        print('removing ' + key)
        del meals[key]
    print(len(meals))


def get_random_proteins(recipes: dict) -> list:
    # randomizing recipe selection
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
    # select three main courses at random
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


def veggie_checker(meals: list, sides: dict, veggies: list = veggies) -> dict:
    # check that each main course recipe has sufficient veggies, if not, pull a recipe at random from the side dish list
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
            checked_meals.append({'type' : 'combo_main', 'obj' : meal})
            checked_meals.append({'type' : 'combo_side', 'obj' : side})
        else:
            checked_meals.append({'type' : 'single_main', 'obj' : meal})
    return checked_meals


def prettify(meals, start):
    """Function converts meal object info into HTML for email
    receives a recipe object or dict of recipe objects"""
    print('Making HTML content from recipe objects.')

    # Import CSS stylesheet
    with open("style.css", "r") as f:
        css = f.read()

    html = f'{css}\t<body>\n'

    for info in meals:
        meal = info['obj'][next(iter(info['obj']))]  # where meal is elements of hhursev recipe-scraper object dict

        title = meal['title']
        if info['type'] == 'combo_main':
            title = f'Main: {title}'
        elif info['type'] == 'combo_side':
            title = f'Side: {title}'
        title = (
            '\t\t<div class="card">\n'
            f'\t\t\t<h1>{title}</h1>\n'
        )

        try:
            servings = f'\t\t\t<i>{meal['yields']}'
        except:
            servings = '\t\t\t<i>servings unknown'

        try:
            host = f' | {meal['site_name']}</i>'
        except:
            host = f' | {meal['host']}</i>'

        title_servings = title + servings + host

        image = (
            '<div class="polaroid">\n'
            f'\t\t\t\t<img src={meal['image']} alt="{meal['title']} from {meal['host']}" />\n'
            '\t\t\t</div>'
        )

        ingredients = ['\t\t\t\t<li>' + i + '</li>' for i in meal['ingredients']]
        ingredients = '\n'.join(ingredients)
        ingredients = (
            '\t\t\t<h2>Ingredients</h2>\n'
            f'\t\t\t<ul>\n{ingredients}\n\t\t\t</ul>'
        )

        instructions = (
            '\t\t\t<h2>Instructions</h2>\n'
            f'\t\t\t<p>{meal['instructions']}</p>\n\t\t</div>\n'
            )

        container = '\n'.join([title_servings, image, ingredients, instructions])
        html = html + container

    elapsed_time = time.time() - start
    if elapsed_time > 1:
        elapsed_time = f'{elapsed_time:.2f} seconds'  # as time in seconds
    else:
        elapsed_time = f'{elapsed_time * 1000:.0f}ms'  # convert from seconds to milliseconds
        
    pretty = (
        f'{html}'
        f'\t\t<p style="color: #888;text-align: center;">Wowza! We found '
        f'{len(unused_main_recipes) + len(unused_side_recipes)} recipes! These {len(meals)} were '
        f'selected at random for your convenience and your family\'s delight. '
        f'It took {elapsed_time} to do this using v14.'
        f'</p>\n</body>\n</html>'
    )
    return pretty


def mailer(content: str, debug_mode: bool) -> None:
    """Function emails pretty formatted meals to recipents, can do BCC
    https://www.justintodata.com/send-email-using-python-tutorial/
    https://docs.python.org/3/library/email.examples.html"""

    msg = MIMEMultipart()
    msg['Subject'] = 'Weekly Meals'
    # Set msg['Bcc'] to SENDER if in debug mode
    msg['Bcc'] = os.getenv('EMAIL_BCC')
    if debug_mode:
        msg['Bcc'] = os.getenv("EMAIL_SENDER")
        
    msg['From'] = os.getenv('EMAIL_SENDER')
    msg.attach(MIMEText(content, 'html'))

    c = ssl.create_default_context()
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465, context=c)
    server.login(os.getenv('EMAIL_SENDER'), os.getenv('EMAIL_PASSWORD'))
    server.set_debuglevel(1)
    server.send_message(msg)
    server.quit()



# START TIMER
start_time = time.time()


# FILENAME CONSTANTS
unused_mains_filename = "unused_mains_recipes.json"
unused_sides_filename = "unused_sides_recipes.json"
used_filename = "used_recipes.json"

debug_mode = check_debug_mode()
if debug_mode:
    selection = debug_list_selection()
    websites = {'debugging': selection}
    unused_main_recipes, unused_side_recipes, scraped_mains, scraped_sides = {}, {}, {}, {}
    unused_main_recipes = load_json(unused_mains_filename)
    print(unused_main_recipes)

else:
    # LOAD PREVIOUSLY COLLECTED DATA
    print('Loading previously collected data')
    unused_main_recipes = load_json(unused_mains_filename)
    unused_side_recipes = load_json(unused_sides_filename)
    used_recipes = load_json(used_filename)

    clean_dictionary(unused_main_recipes)
    clean_dictionary(unused_side_recipes)
    sys.exit()

    # CHECK RECENCY OF PREVIOUSLY COLLECTED DATA
    if is_file_old(unused_mains_filename, 12):
        print(f'{unused_mains_filename} is old, getting fresh data')
        # SCRAPE FRESH DATA IF EXISTING DATA IS OLD
        unused_main_recipes, unused_side_recipes = get_fresh_data(websites)
        save_json(unused_mains_filename, unused_main_recipes)
        save_json(unused_sides_filename, unused_side_recipes)

    # SORT BY PROTEIN AND RETURN LIST OF THREE RANDOM MEALS
    print('Getting meals with select proteins at random')
    randomized_meals = get_random_proteins(unused_main_recipes)

    # ENSURE MEALS HAVE ADEQUATE VEGGIES OR ADD A SIDE
    print('Checking for veggies')
    meals = veggie_checker(randomized_meals, unused_side_recipes)
    for meal in meals:
        for value in meal['obj'].values():
            print(meal['obj'])
            print(meal['type'].upper() + " : " + value['title'])

    # PRETTYIFY THE MEALS INTO EMAILABLE HTML BODY
    print('Prettifying meals into HTML')
    pretty = prettify(meals, start_time)
    
    # SEND EMAIL
    print('Emailing recipients')
#    mailer(pretty, debug_mode)

    # UPDATE RESOURCE LISTS
    print(meals)
    sys.exit()
    
    # SAVE OUT DICTIONARIES AS FILES FOR REUSE
    print('Saving out files')
    save_json(unused_mains_filename, unused_main_recipes)
    save_json(unused_sides_filename, unused_side_recipes)
