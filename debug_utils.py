"""Debug mode utilities."""

import argparse
import json


def check_debug_mode() -> bool:
    """Check for debug mode or default to full mode."""
    parser = argparse.ArgumentParser(description="Check for debug mode")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    if args.debug:
        print("Debug mode detected")
        return True
    return False


def debug_list_selection(websites: dict) -> dict:
    """When in debug mode, tell user what website titles are in the dictionary."""
    print("The websites list supports the following sites:")
    for n, website in enumerate(websites):
        # note we increment by 1 to make output more user-friendly
        print(f"{n + 1}\t{website}")
    while True:
        try:
            # prompt user to enter the index of the list they wish to debug
            number = int(input("Which website would you like to debug? (#) "))
            # only accept input that would fall within the indices of
            # the dictionary. Recall the increment from above
            if 0 < number < len(websites) + 1:
                # account for the increment when saving user selection
                selection = list(websites)[number - 1]
                break
            raise ValueError
        except ValueError:
            print("I'm sorry, that wasn't a valid number.")
    # show user what they've selected before proceeding
    print(f"You've selected to debug {selection}.")
    print("The dictionary entry is:")
    print(json.dumps(websites[selection], indent=4))
    return websites[selection]