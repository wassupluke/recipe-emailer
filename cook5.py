from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage
from recipe_scrapers import scrape_me
from email.mime.text import MIMEText
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from random import randrange
import requests
import smtplib
import time
import ssl
import os
import re


def make_soup(site):
    h = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    response = requests.get(site,headers=h)
    html = response.content
    soup = BeautifulSoup(html,'html.parser')
    return soup


def scrape_by_class(soup,c,rb):
    recipes = soup('a',class_=c)
    for a in recipes:
        s = str(a)
        title = a.text
        l = re.search(r'href="(\S+)"',s)
        link = l.group(1)
        if 'plan' in link.lower():
            pass
        elif '30-whole30-meals-in-30-minutes' in link.lower():
            pass
        else:
            rb.append(link)
    return rb


def scrape_by_style(soup,y,rb):
    recipes = soup('a',style=y)
    for a in recipes:
        s = str(a)
        title = a.text
        l = re.search(r'href="(\S+)"',s)
        link = l.group(1)
        rb.append(link)
    return rb


def scrape_by_h2(soup,y,rb):
    recipes = soup('h2',class_=y)
    for a in recipes:
        s = str(a)
        title = a.text
        l = re.search(r'href="(\S+)"',s)
        link = l.group(1)
        if 'plan' in link.lower():
            pass
        else:
            rb.append(link)
    return rb


def scrape_by_h3(soup,y,rb):
    recipes = soup('h3',class_=y)
    for a in recipes:
        s = str(a)
        title = a.text
        l = re.search(r'href="(\S+)"',s)
        link = l.group(1)
        if 'plan' in link.lower():
            pass
        elif 'recipes' in link.lower():
            pass
        else:
            rb.append(link)
    return rb


def scrape_by_parent(soup,y,rb):
    recipes = soup('article',class_=y)
    for a in recipes:
        s = str(a)
        title = a.text
        l = re.search(r'href="(\S+)"',s)
        link = l.group(1)
        if 'plan' in link.lower():
            pass
        elif 'recipes' in link.lower():
            pass
        else:
            rb.append(link)
    return rb


def prettify(meals):
    all_recipes = []
    for meal in meals:
        title = meal.title()
        Title = f'<h1>{title}</h1>'
        ingredients = ["<li>" + i + "</li>" for i in meal.ingredients()]
        Ingredients = '\n'.join(ingredients)
        Ingredients = f'<h3>Ingredients</h3>{Ingredients}'
        instructions = meal.instructions()
        Instructions = f'<h3>Instructions</h3>\n<p>{instructions}</p>'
        recipe = [Title, Ingredients, Instructions]
        full_recipe = '\n\n'.join(recipe)
        all_recipes.append(full_recipe)
    recipes_for_email = '\n\n'.join(all_recipes)
    return recipes_for_email


def mailer(pretty):  # https://www.justintodata.com/send-email-using-python-tutorial/
    load_dotenv()  # take environment variables from .env
    
    email_sender = os.getenv("EMAIL_SENDER")
    email_password = os.getenv("EMAIL_PASSWORD")
    email_receiver = os.getenv("EMAIL_RECEIVER")

    subject = 'Weekly Meals'
    body = (pretty)

    email_message = MIMEMultipart()
    email_message['From'] = email_sender
    email_message['To'] = email_receiver
    email_message['Subject'] = subject
    
    email_message.attach(MIMEText(body, "html"))
    # Convert it to a string
    email_string = email_message.as_string()

    # Connect to the Gmail SMTP server and Send Email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(email_sender, email_password)
        server.sendmail(email_sender, email_receiver, email_string)


if __name__ == "__main__":
    start = time.time()

    # Make a blank list to hold links to recipes (rb for recipebook)
    recipebook = []

    # Info about how to process scraping recipe links each site
    sites_to_scrape = [
            ['a class',
             'https://www.reciperunner.com/category/recipes/dinners/',
             'wpp-post-title'],
            ['a class',
            'https://www.paleorunningmomma.com/course/dinner/',
            'entry-title-link'],
            ['h2 class',
             'https://www.skinnytaste.com/?_course=dinner-recipes',
             'entry-title'],
            ['h3 class',
             'https://www.skinnytaste.com/recipes/dinner-recipes/',
             'entry-title'],
            ['h2 class',
             'https://www.twopeasandtheirpod.com/category/recipes/main-dishes/',
             'post-summary__title'],
            ['h3 class',
             'https://www.wellplated.com/category/recipes-by-type/entreesmain-dishes/#recent',
             'post-summary__title'],
            ['a class',
             'https://www.thespruceeats.com/dinner-4162806',
             'comp mntl-card-list-items mntl-document-card mntl-card card card--no-image'],
             ['a class',
             'https://nourishedbynutrition.com/recipe-index/?_sft_category=entrees',
             'post'],
             ['h2 class',
             'https://www.eatingbirdfood.com/category/meal-type/dinnerlunch/',
             'post-summary__title'],
             ['parent class',
             'https://www.budgetbytes.com/recipe-catalog/?fwp_by_course=main-dish',
             'post-summary post-summary--secondary']
            ]

    # short list for debugging
    debug_to_scrape = [
            ['parent class',
             'https://www.budgetbytes.com/recipe-catalog/?fwp_by_course=main-dish',
             'post-summary post-summary--secondary']
            ]

    # Not yet usable on recipe_scrapers
    wild_sites = [
        ['a style',
             'https://www.dishingouthealth.com/category/recipes/dinner/',
             'text-decoration: none;']
        ]

    for site in sites_to_scrape:
        soup = make_soup(site[1])
        if site[0] == 'a class':
            scrape_by_class(soup,site[2],recipebook)
        elif site[0] == 'a style':
            scrape_by_style(soup,site[2],recipebook)
        elif site[0] == 'h2 class':
            scrape_by_h2(soup,site[2],recipebook)
        elif site[0] == 'h3 class':
            scrape_by_h3(soup,site[2],recipebook)
        elif site[0] == 'parent class':
            scrape_by_parent(soup,site[2],recipebook)
        else:
            pass

    # A blank list to hold scrape objects after they're run through recipe_scrapers
    scraperbook = []

    # Lists to hold sorted recipes
    seafood_meals = []
    landfood_meals = []

    for recipe in recipebook:
        scraper = scrape_me(recipe)
        scraperbook.append(scraper)
        for ingredient in scraper.ingredients():
            if 'salmon' in ingredient.lower():
                seafood_meals.append(scraper)
            elif 'shrimp' in ingredient.lower():
                seafood_meals.append(scraper)
            elif 'chicken' in ingredient.lower():
                landfood_meals.append(scraper)
            elif 'pork' in ingredient.lower():
                landfood_meals.append(scraper)
            elif 'turkey' in ingredient.lower():
                landfood_meals.append(scraper)
            else:
                pass

    meals = []

    meals.append(landfood_meals.pop(randrange(len(landfood_meals))))
    meals.append(landfood_meals[randrange(len(landfood_meals))])
    meals.append(seafood_meals[randrange(len(seafood_meals))])

    pretty = prettify(meals)

    mailer(pretty)

    print(time.time() - start)
        
    """
    dishingouthealth :: DONE  :: NOT ON RECIPE_SCRAPER
    paleorunningmamma :: DONE
    reciperunner :: DONElandfood_meals.pop(0)
    landfood_meals.pop(0)
    skinnytaste  :: DONE
    twopeasandtheirpod  :: DONE
    slimmingeats  :: NOT ON RECIPE_SCRAPER
    cleanfoodcrush :: NOT ON RECIPE_SCRAPER
    thereciperebel :: NOT ON RECIPE_SCRAPER
    wellplated  :: DONE
    saltandlavender :: NOT ON RECIPE_SCRAPER
    wowstaceyhawkins :: NOT ON RECIPE_SCRAPER
    thespruceeats :: DONE
    nourishedbynutrition :: DONE
    eatingbirdfood :: DONE
    budgetbytes :: DONE
    """

