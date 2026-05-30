"""Recipe selection and filtering logic.

This module handles selecting recipes based on protein type and
ensuring adequate vegetable content.
"""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any, TypeAlias

from config import (
    LANDFOOD_COUNT_NO_SEAFOOD,
    LANDFOOD_COUNT_WITH_SEAFOOD,
    LANDFOOD_PROTEINS,
    SEAFOOD_COUNT,
    SEAFOOD_PROTEINS,
)
from seasonal_selection import final_score, weighted_sample

if TYPE_CHECKING:
    from datetime import date as _date

__all__ = ["select_random_proteins", "ensure_veggies", "InsufficientRecipesError"]

logger = logging.getLogger(__name__)

# Type aliases for clarity
RecipeDict: TypeAlias = dict[str, Any]
RecipeItem: TypeAlias = dict[str, RecipeDict]
MealItem: TypeAlias = dict[str, str | RecipeItem]


class InsufficientRecipesError(Exception):
    """Raised when there aren't enough recipes to fulfill requirements."""

    pass


def select_random_proteins(
    recipes: dict[str, RecipeDict], today: _date | None = None
) -> list[RecipeItem]:
    """Select recipes randomly based on protein categorization.

    Categorizes recipes as seafood or land-based protein, then selects
    a balanced mix according to configured counts.

    Args:
        recipes: Dictionary mapping URLs to recipe data

    Returns:
        List of selected recipe items, each a dict with URL as key

    Raises:
        InsufficientRecipesError: If not enough valid recipes available

    Example:
        >>> recipes = {
        ...     "url1": {"ingredients": ["chicken", "salt"]},
        ...     "url2": {"ingredients": ["salmon", "dill"]},
        ... }
        >>> selected = select_random_proteins(recipes)
        >>> len(selected)
        3
    """
    if today is None:
        from datetime import datetime

        today = datetime.now().date()

    seafood_recipes: list[RecipeItem] = []
    landfood_recipes: list[RecipeItem] = []

    # Categorize recipes by protein type
    for url, recipe_data in recipes.items():
        try:
            ingredients = recipe_data.get("ingredients", [])
            if not isinstance(ingredients, list):
                logger.warning(f"Recipe {url} has invalid ingredients: {ingredients}")
                continue

            protein_type = _categorize_by_protein(ingredients)
            recipe_item = {url: recipe_data}

            if protein_type == "seafood":
                seafood_recipes.append(recipe_item)
            elif protein_type == "landfood":
                landfood_recipes.append(recipe_item)

        except (TypeError, AttributeError) as e:
            logger.warning(f"Skipping invalid recipe {url}: {e}")
            continue

    # Select appropriate mix using weighted-random by seasonal score
    selected = _select_meal_mix(seafood_recipes, landfood_recipes, today)

    logger.info(
        f"Selected {len(selected)} recipes: "
        f"{sum(1 for r in selected if _has_seafood_protein(r))} seafood, "
        f"{len(selected) - sum(1 for r in selected if _has_seafood_protein(r))} landfood"
    )

    return selected


def _categorize_by_protein(ingredients: list[str]) -> str | None:
    """Determine if recipe contains seafood or land-based protein.

    Args:
        ingredients: List of ingredient strings

    Returns:
        "seafood", "landfood", or None if no protein found
    """
    for ingredient in ingredients:
        ingredient_lower = ingredient.lower()

        # Seafood takes precedence
        if any(protein in ingredient_lower for protein in SEAFOOD_PROTEINS):
            return "seafood"

        if any(protein in ingredient_lower for protein in LANDFOOD_PROTEINS):
            return "landfood"

    return None


def _has_seafood_protein(recipe_item: RecipeItem) -> bool:
    """Check if a recipe item contains seafood protein."""
    for recipe_data in recipe_item.values():
        ingredients = recipe_data.get("ingredients", [])
        return _categorize_by_protein(ingredients) == "seafood"
    return False


def _select_meal_mix(
    seafood: list[RecipeItem], landfood: list[RecipeItem], today: _date
) -> list[RecipeItem]:
    """Select a seasonally-weighted mix of seafood and landfood meals.

    Preserves the protein balance (2 landfood + 1 seafood, or 3 landfood when no
    seafood) but draws within each category by weighted-random on final_score.

    Raises:
        InsufficientRecipesError: If requirements cannot be met
    """
    # Case 1: Sufficient meals of both types
    if len(landfood) >= LANDFOOD_COUNT_WITH_SEAFOOD and len(seafood) >= SEAFOOD_COUNT:
        land_pick = weighted_sample(
            landfood,
            [final_score(_recipe_of(item), today) for item in landfood],
            LANDFOOD_COUNT_WITH_SEAFOOD,
        )
        sea_pick = weighted_sample(
            seafood,
            [final_score(_recipe_of(item), today) for item in seafood],
            SEAFOOD_COUNT,
        )
        return land_pick + sea_pick

    # Case 2: Sufficient landfood, no seafood
    if len(landfood) >= LANDFOOD_COUNT_NO_SEAFOOD and len(seafood) == 0:
        return weighted_sample(
            landfood,
            [final_score(_recipe_of(item), today) for item in landfood],
            LANDFOOD_COUNT_NO_SEAFOOD,
        )

    # Case 3: Insufficient recipes
    error_msg = (
        f"Insufficient recipes: {len(landfood)} landfood, {len(seafood)} seafood. "
        f"Need {LANDFOOD_COUNT_NO_SEAFOOD} landfood or "
        f"{LANDFOOD_COUNT_WITH_SEAFOOD} landfood + {SEAFOOD_COUNT} seafood."
    )
    logger.error(error_msg)
    raise InsufficientRecipesError(error_msg)


def _recipe_of(recipe_item: RecipeItem) -> RecipeDict:
    """Unwrap the recipe dict from a {url: recipe} item."""
    return recipe_item[next(iter(recipe_item))]


def ensure_veggies(
    meals: list[RecipeItem],
    side_dishes: dict[str, RecipeDict],
    required_veggies: tuple[str, ...],
) -> list[MealItem]:
    """Ensure each meal has adequate vegetables, adding sides if needed.

    Args:
        meals: List of selected main dish recipe items
        side_dishes: Dictionary of available side dish recipes
        required_veggies: Tuple of vegetable keywords to check for

    Returns:
        List of meal items with type annotations:
        - "single_main": Main dish with sufficient veggies
        - "combo_main": Main dish lacking veggies (paired with side)
        - "combo_side": Side dish added to provide veggies

    Example:
        >>> meals = [{"url": {"ingredients": ["chicken"]}}]
        >>> sides = {"side_url": {"ingredients": ["broccoli"]}}
        >>> veggies = ("broccoli",)
        >>> result = ensure_veggies(meals, sides, veggies)
        >>> len(result)
        2  # Main + side
    """
    processed_meals: list[MealItem] = []

    for meal_item in meals:
        if _has_sufficient_veggies(meal_item, required_veggies):
            processed_meals.append({"type": "single_main", "obj": meal_item})
            logger.debug(f"Meal has sufficient veggies: {list(meal_item.keys())[0]}")
        else:
            # Add a random side dish
            if not side_dishes:
                logger.warning("No side dishes available to add veggies")
                processed_meals.append({"type": "single_main", "obj": meal_item})
                continue

            side_url, side_data = random.choice(list(side_dishes.items()))  # nosec B311
            side_item = {side_url: side_data}

            processed_meals.append({"type": "combo_main", "obj": meal_item})
            processed_meals.append({"type": "combo_side", "obj": side_item})
            logger.debug(
                f"Added side dish {side_url} to meal {list(meal_item.keys())[0]}"
            )

    return processed_meals


def _has_sufficient_veggies(
    meal_item: RecipeItem, required_veggies: tuple[str, ...]
) -> bool:
    """Check if a meal contains any of the required vegetables.

    Args:
        meal_item: Recipe item to check
        required_veggies: Tuple of veggie keywords

    Returns:
        True if meal contains at least one required veggie
    """
    for recipe_data in meal_item.values():
        ingredients = recipe_data.get("ingredients", [])

        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            if any(veggie in ingredient_lower for veggie in required_veggies):
                return True

    return False
