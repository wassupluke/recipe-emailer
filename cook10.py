#!/usr/bin/env python3

'''Import modules'''
import time
import ssl
import os
import re
from css import head
from lists import full, debug, veggie_list
from random import randrange, choice, sample
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from recipe_scrapers import scrape_me
import json
import requests
import logging
from dotenv import load_dotenv
from bs4 import BeautifulSoup


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
                print(f"Recipe {ms.index(m)} needs veggies")
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
       # print(f"\t{s[3][:69]...}")
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


def prettify_neat(m, ar, x):
    '''Function converts meal object info into HTML for email'''
    title = m.title()
    if x == 0:
        title = f"Main: {title}"
    elif x == 1:
        title = f"Side: {title}"
    else:
        pass
    title = f"<section><h1>{title}</h1>"
    try:
        servings = f"<i>{m.yields()}</i>"
    except:
        servings = "<i>servings unknown</i>"
    title_servings = title + servings
    ingredients = ["<li>" + i + "</li>" for i in m.ingredients()]
    ingredients = "\n".join(ingredients)
    ingredients = f"<h3>Ingredients</h3><ul>{ingredients}</ul>"
    instructions = m.instructions()
    instructions = f"<h3>Instructions</h3>\n<p>{instructions}</p></section>"
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
    msg['Bcc'] = os.getenv('EMAIL_RECEIVER')  # BCC_RECEIVER or EMAIL_RECEIVER
    msg.attach(MIMEText(p, "html"))

    c = ssl.create_default_context()
    server = smtplib.SMTP_SSL('smtp.gmail.com',465,context=c)
    server.login(me, os.getenv('EMAIL_PASSWORD'))
    server.set_debuglevel(1)
    server.send_message(msg)
    server.quit()


#-----------------------------------------------------------------#

if __name__ == "__main__":

    # Initilize logging
    logging.basicConfig(filename='error.log', level=logging.DEBUG)
    
    try:
        source_list = debug  # full or debug
        start = time.time()

        # load or create unused recipe file
        try:
            with open('unused_recipes.json') as f:
                recipebook = json.load(f)
        except FileNotFoundError:
            recipebook = []
            with open('unused_recipes.json', 'a') as f:
                json.dump([],f)

        # load or create used recipe file
        try:
            with open('used_recipes.json') as f:
                used = json.load(f)
        except FileNotFoundError:
            used = []
            with open('used_recipes.json', 'a') as f:
                json.dump([],f)

        # gets all recipes from each site in source_list
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

        # A blank list to hold scrape objects after they're
        # run through recipe_scrapers
        scraperbook = {}

        # Lists to hold sorted recipes
        seafood_meals = []
        landfood_meals = []

        # get recipe_scrapers object for each recipe
        # and sort by protein
        print('cooking up recipe objects')
        for recipe in unused:
            print(f'\t{recipe[:69]}...')
            scraper = scrape_me(recipe)
            scraperbook[scraper] = recipe
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

        # build list of three random meals
        meals = []
        print(seafood_meals)
        print(landfood_meals)
        if len(seafood_meals) > 0:
            if len(landfood_meals) > 1:
                meals.append(choice(seafood_meals))
                [meals.append(s) for s in sample(landfood_meals, 2)]
        elif len(landfood_meals) > 2:
            [meals.append(s) for s in sample(landfood_meals, 3)]
        else:
            raise EOFError

        # ensure each meal has at least one veggie from veggie_list
        meals, sidebook = veggie_checker(meals, source_list, veggie_list)
            
        # prettify recipes with HTML
        print('making HTML content from recipe objects')
        all_recipes = []
        for meal in meals:
            if not isinstance(meal, list):
                used.append(scraperbook.get(meal))  # update used list
                prettify_neat(meal, all_recipes, None)
            else:
                for mea in meal:
                    prettify_neat(mea, all_recipes, meal.index(mea))
                used.append(scraperbook.get(meal[0]))  # update used list
        unused = [u for u in unused if u not in used]  # update unused list
        print(f'len unused: {len(unused)}')
        print(f'len used: {len(used)}')   
        pretty = "\n\n".join(all_recipes)
        total_sites_line = (
            f'<p style="color: #888;">Wowza! We found '
            f"{len(recipebook) + len(scraperbook)} recipes! "
            f"These {len(meals)} were selected at random for "
            f"your convenience and your family's delight. "
            f"It took {(time.time() - start):.2f} seconds to do "
            f"it using v10</p>"
            )
        prettiest = f"{head}<body>{pretty}\n\n{total_sites_line}</body></html>"
        print(prettiest)
        
        # save unused recipes to file
        with open('unused_recipes.json', 'w') as f:
            json.dump(unused, f)

        # save sent recipes to file
        with open('used_recipes.json', 'w') as f:
            json.dump(used, f)

        # email the prettiest HTML to msg['Bcc']
        print(f'trying to email the list')
        mailer(prettiest)
        
    except Exception as e:
        with open('error.log', 'w') as f:
            f.write('')  # clears existing logs
        logging.exception('Code failed, see below.')
        raise
        
