
# RECIPE EMAILER

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/781c45297c44456791ac9063099554cb)](https://app.codacy.com/gh/wassupluke/recipe-emailer/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

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

```text
SENDER=<yourEmail@AddressHere.com>
PASSWD=see <https://myaccount.google.com/apppasswords>
BCC=<first@recipient.com>,<second@recipient.com>,etc
```
