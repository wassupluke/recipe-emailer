# RECIPE EMAILER

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/0af9ede41ed446d0a15fcaee8e93c371)](https://app.codacy.com/gh/wassupluke/recipe-emailer?utm_source=github.com&utm_medium=referral&utm_content=wassupluke/recipe-emailer&utm_campaign=Badge_Grade)

## About

Scrapes wife's favorite recipe sites for recipes and emails her three random
recipes each week. The program will check that each entree sent has sufficient
vegetables. If an entree lacks good veggies (i.e., those listed in veggies.py)
it will grab a side dish at random to put with the meal.

## Requirements

- python
- python_dotenv (pip install)
- bs4 (pip install)
- recipe_scrapers (pip install)
- a .env file in the same directory as the script in the format:

'''
SENDER=<yourEmail@AddressHere.com>
PASSWD=see <https://myaccount.google.com/apppasswords>
BCC=<first@recipient.com>,<second@recipient.com>,etc
'''
