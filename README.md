
# RECIPE EMAILER

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/781c45297c44456791ac9063099554cb)](https://app.codacy.com/gh/wassupluke/recipe-emailer/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

## About

Scrapes wife's favorite recipe sites for recipes and emails her three random
recipes each week. The program will check that each entrée sent has sufficient
vegetables. If an entrée lacks good veggies (i.e., those listed in veggies.py)
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
# Recipe Scraper - Modular Project Structure

## Directory Structure

```
recipe_scraper/
├── main.py                    # Main entry point
├── config.py                  # Configuration and constants
├── debug_utils.py             # Debug mode utilities
├── file_utils.py              # File I/O operations
├── web_scraper.py             # Web scraping functions
├── recipe_processor.py        # Recipe data fetching logic
├── recipe_selector.py         # Recipe selection algorithms
├── html_generator.py          # HTML email generation
├── email_sender.py            # Email sending functionality
├── lists.py                   # Website and veggie lists (existing)
├── style.css                  # Email styling (existing)
├── .env                       # Environment variables (existing)
└── requirements.txt           # Python dependencies
```

## Module Breakdown

### `config.py`
- All constants and configuration values
- Environment variable loading
- Version number
- File paths
- Email settings
- HTTP headers and timeouts

### `debug_utils.py`
- `check_debug_mode()` - Parse command-line arguments
- `debug_list_selection()` - Interactive website selection for debugging

### `file_utils.py`
- `save_json()` - Save dictionaries to JSON files
- `load_json()` - Load JSON files into dictionaries
- `is_file_old()` - Check file age

### `web_scraper.py`
- `get_html()` - Fetch HTML from URLs
- `get_recipe_urls()` - Extract recipe URLs from site pages
- `cleanup_recipe_urls()` - Filter and fix malformed URLs
- `scraper()` - Parse recipe data using recipe-scrapers library

### `recipe_processor.py`
- `get_fresh_data()` - Orchestrate the entire scraping process
- Handles URL deduplication and filtering
- Coordinates HTML fetching and parsing

### `recipe_selector.py`
- `get_random_proteins()` - Select meals by protein type
- `veggie_checker()` - Ensure meals have vegetables, add sides if needed

### `html_generator.py`
- `prettify()` - Generate HTML email content from recipe objects

### `email_sender.py`
- `mailer()` - Send emails via SMTP

### `main.py`
- Program entry point
- Orchestrates all modules
- Error handling and logging

## Benefits of This Structure

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Easier Testing**: Individual functions can be tested in isolation
3. **Maintainability**: Changes to one aspect (e.g., email) don't affect others
4. **Reusability**: Modules can be imported and used in other projects
5. **Readability**: Smaller files are easier to navigate and understand
6. **Configuration Management**: All constants in one place

## Running the Program

```bash
# Normal mode
python main.py

# Debug mode
python main.py -d
```

## Dependencies

Make sure your `requirements.txt` includes:
```
requests
python-dotenv
recipe-scrapers
tqdm
```

## Environment Variables Required

The `.env` file should contain:
```
SENDER=your-email@gmail.com
PASSWD=your-app-password
BCC=recipient1@example.com,recipient2@example.com
```