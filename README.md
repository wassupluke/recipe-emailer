
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

```markdown
SENDER=yourEmail@AddressHere.com
PASSWD=*
BCC=first@recipient.com,second@recipient.com,etc
```
\* see [Google App Passwords](https://myaccount.google.com/apppasswords)

## Automating / Scripting / Cron

Change the user directory to your needs, or try simplifying to `$HOME/code/recipe-emailer/cook.sh`

```bash
0 8 * * Fri ./home/wassu/code/recipe-emailer/cook.sh
```

## Broken after upgrading python 3.11 to 3.13?

You may need to recreate the virtual environment.

```bash
cd /home/wassu/code/recipe-emailer
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip --version  # to verify pip works
pip install -r requirements.txt
```
