"""A collection of debugging tools for recipe emailer."""

import argparse


def check_debug_mode() -> bool:
    """Check if one of the following debug flags were used when running script.

    -d
    --debug
    """
    parser = argparse.ArgumentParser(description="Check for debug mode")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    if args.debug:
        print("Debug mode detected")
        return True
    return False


def list_debug_options(websites: dict[str, dict[str, str]]) -> dict[str, str]:
    """List websites for debugging.

    If in debug mode, tell the user what keys (website title) are in the
    dictonary along with their index.
    """
    print("The websites list supports the following sites:")
    for n, website in enumerate([key for key in websites]):
        # note we increment by 1 to make output more user-friendly
        print(f"{n + 1}\t{website}")
    while True:
        try:
            # prompt user to enter the index of the list they wish to debug
            number = int(input("Which website would you like to debug? (#) "))
            # only accept input that would fall within the indicies of
            # the dictionary. Recall the increment from above
            if 0 < number < len(websites) + 1:
                # account for the increment when saving user selection
                selection = list(websites)[number - 1]
                break
            raise ValueError
        except ValueError:
            print("I'm sorry, that wasn't a valid number.")
    # show user what they've selected before proceeding
    print(f"You've selectected to debug {selection}.")
    return websites.get(selection, {})
