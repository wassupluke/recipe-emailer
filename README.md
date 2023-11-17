# recipe_scraper
scrapes wife's favorite recipe sites for recipes and emails her three random ones each week

# requirements:
- python
- python_dotenv (pip install)
- bs4 (pip install)
- recipe_scrapers (pip install)
- a .env file in the same directory as the script in the format:<br/>
  EMAIL_SENDER=yourEmailAddressHere<br/>
  EMAIL_PASSWORD=iForgetWhereIGotThis<br/>
  EMAIL_BCC=firstRecipient,secondRecipient,etc
