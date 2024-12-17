# recipe-emailer
scrapes wife's favorite recipe sites for recipes and emails her three random ones each week

# requirements:
  - python
  - python_dotenv (pip install)
  - bs4 (pip install)
  - recipe_scrapers (pip install)
  - a .env file in the same directory as the script in the format:<br/>
    SENDER=<yourEmail@AddressHere.com><br/>
    PASSWD=see https://myaccount.google.com/apppasswords<br/>
    BCC=<first@recipient.com>,<second@recipient.com>,etc
