"""Recipe selection and filtering logic."""

import random
import sys

from config import (
    SEAFOOD_PROTEINS,
    LANDFOOD_PROTEINS,
    LANDFOOD_COUNT_WITH_SEAFOOD,
    SEAFOOD_COUNT,
    LANDFOOD_COUNT_NO_SEAFOOD,
)


def get_random_proteins(recipes: dict) -> list:
    """Randomize recipe selection based on protein types."""
    seafood, landfood = [], []
    for recipe in recipes.items():
        try:
            for ingredient in recipe[1]["ingredients"]:
                ingredient_lower = ingredient.lower()

                # Check if recipe contains seafood proteins
                if any(protein in ingredient_lower for protein in SEAFOOD_PROTEINS):
                    seafood.append({recipe[0]: recipe[1]})
                    break  # Found seafood, no need to check landfood

                # Check if recipe contains land-based proteins
                elif any(protein in ingredient_lower for protein in LANDFOOD_PROTEINS):
                    landfood.append({recipe[0]: recipe[1]})
                    break  # Found landfood, move to next recipe

        except TypeError:
            print(f"needs removed: {recipe}, not valid recipe")

    # Shuffle the lists
    random.shuffle(landfood)
    random.shuffle(seafood)

    # Select meals based on availability
    if len(landfood) > LANDFOOD_COUNT_WITH_SEAFOOD and len(seafood) > 0:
        landfood = random.sample(landfood, LANDFOOD_COUNT_WITH_SEAFOOD)
        seafood = random.sample(seafood, SEAFOOD_COUNT)
    elif len(landfood) > LANDFOOD_COUNT_NO_SEAFOOD and len(seafood) == 0:
        landfood = random.sample(landfood, LANDFOOD_COUNT_NO_SEAFOOD)
    else:
        print(
            "Somehow we ended up with no seafood meals and two or less "
            "landfood meals. Can't do anything with nothing. Exiting."
        )
        sys.exit()

    return landfood + seafood


def veggie_checker(meals: list, sides: dict, veggies: list) -> list:
    """Check that each main course recipe has sufficient veggies.

    If not, pull a recipe at random from the side dish list.
    """
    checked_meals = []
    for meal in meals:
        has_veggies = False
        key = next(iter(meal))
        for ingredient in meal[key]["ingredients"]:
            if any(veggie in ingredient.lower() for veggie in veggies):
                has_veggies = True
                break
        if not has_veggies:
            side = random.choice(list(sides.items()))
            side = {side[0]: side[1]}
            checked_meals.append({"type": "combo_main", "obj": meal})
            checked_meals.append({"type": "combo_side", "obj": side})
        else:
            checked_meals.append({"type": "single_main", "obj": meal})
    return checked_meals