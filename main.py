#!/usr/bin/env python3

"""A program I wrote to save my wife time and headache.

This program grabs recipes from all her favorite sites
and sends her a few to make each week. Now she doesn't
have to spend her time looking up what to make, it's all
automagic!
"""

import logging
import time
from datetime import datetime

# IMPORT LOCAL MODULES
from config import (
    UNUSED_MAINS_FILENAME,
    UNUSED_SIDES_FILENAME,
    FAILED_FILENAME,
    USED_FILENAME,
    FILE_AGE_THRESHOLD,
    VEGGIES
)
from debug_utils import check_debug_mode, debug_list_selection
from file_utils import save_json, load_json, is_file_old
from recipe_processor import get_fresh_data
from recipe_selector import get_random_proteins, veggie_checker
from html_generator import prettify
from email_sender import mailer

# IMPORT LISTS
from websites import WEBSITES


def main():
    """Main execution function."""
    # START TIMER
    start_time = time.time()

    try:
        date = datetime.today().strftime("%Y-%m-%d")
        print(date)  # for logging purposes

        debug_mode = check_debug_mode()

        if debug_mode:
            selection = debug_list_selection(WEBSITES)
            websites_to_use = {
                "debugging": selection
            }  # redefine websites list for debug session
            unused_main_recipes, unused_side_recipes = {}, {}
            failed_recipes, used_recipes = {}, {}
            mains_was_created = False
            sides_was_created = False
            needs_fresh_data = True
        else:
            websites_to_use = WEBSITES
            # LOAD PREVIOUSLY COLLECTED DATA
            print("Loading previously collected data")
            unused_main_recipes, mains_was_created = load_json(UNUSED_MAINS_FILENAME)
            unused_side_recipes, sides_was_created = load_json(UNUSED_SIDES_FILENAME)
            failed_recipes, _ = load_json(FAILED_FILENAME)
            used_recipes, _ = load_json(USED_FILENAME)

            # CHECK RECENCY OF PREVIOUSLY COLLECTED DATA
            # for this instance, files are considered old after 12 hours
            # Also get fresh data if files were just created (empty)
            needs_fresh_data = (
                    mains_was_created
                    or sides_was_created
                    or is_file_old(UNUSED_MAINS_FILENAME, FILE_AGE_THRESHOLD)
            )

        if needs_fresh_data:
            if mains_was_created or sides_was_created:
                print("Recipe files were just created, getting fresh data")
            else:
                print(UNUSED_MAINS_FILENAME, "is old, getting fresh data")
            # SCRAPE FRESH DATA IF EXISTING DATA IS OLD
            unused_main_recipes, unused_side_recipes = get_fresh_data(
                websites_to_use,
                unused_main_recipes,
                unused_side_recipes,
                used_recipes,
                failed_recipes,
                debug_mode,
            )  # heart of the program
            if not debug_mode:
                save_json(UNUSED_MAINS_FILENAME, unused_main_recipes)
                save_json(UNUSED_SIDES_FILENAME, unused_side_recipes)


        # SORT BY PROTEIN AND RETURN LIST OF THREE RANDOM MEALS
        print("Getting meals with select proteins at random")
        randomized_meals = get_random_proteins(unused_main_recipes)

        # ENSURE MEALS HAVE ADEQUATE VEGGIES OR ADD A SIDE
        print("Checking for veggies")
        meals = veggie_checker(randomized_meals, unused_side_recipes, VEGGIES)

        # PRETTIFY THE MEALS INTO EMAILABLE HTML BODY
        print("Prettifying meals into HTML")
        pretty = prettify(
            meals,
            start_time,
            len(unused_main_recipes),
            len(unused_side_recipes),
        )

        # SEND EMAIL
        print("Emailing recipients")
        mailer(pretty, debug_mode)

        if not debug_mode:
            # UPDATE THE RESOURCE FILES BEFORE SAVING OUT
            for meal in meals:
                try:
                    url = next(iter(meal["obj"]))
                    used_recipes[url] = date
                    if url in unused_main_recipes:
                        del unused_main_recipes[url]
                    elif url in unused_side_recipes:
                        del unused_side_recipes[url]
                    else:
                        raise KeyError
                except KeyError:
                    print(
                        f"{meal} URL was not in the main or side lists, "
                        "so not removing"
                    )
            print(
                f"main {len(unused_main_recipes)} final\n"
                f"side {len(unused_side_recipes)} final"
            )

            # SAVE OUT DICTIONARIES AS FILES FOR REUSE
            print("Saving out files")
            save_json(UNUSED_MAINS_FILENAME, unused_main_recipes)
            save_json(UNUSED_SIDES_FILENAME, unused_side_recipes)
            save_json(FAILED_FILENAME, failed_recipes)
            save_json(USED_FILENAME, used_recipes)

    except Exception as e:
        with open("error.log", "w+") as f:
            # clear existing logs
            f.write("")
            logging.exception("Code failed, see below: %s", e)
            error_content = "<br />".join(list(f.readlines()))
            mailer(error_content, True)
        raise


if __name__ == "__main__":
    main()