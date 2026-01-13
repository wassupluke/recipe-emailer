"""HTML generation for email content."""

import time
from config import VERSION


def prettify(meals: list, start: float, unused_main_count: int, unused_side_count: int) -> str:
    """Convert meal object info into HTML for email.

    Receives a recipe object or dict of recipe objects.
    """
    print("Making HTML content from recipe objects.")

    # Import HTML header containing CSS stylesheet.
    with open("head.html", "r") as f:
        head = f.read()

    html = f"{head}\t<body>\n"

    for info in meals:
        meal = info["obj"][
            next(iter(info["obj"]))
        ]  # where meal is elements of hhursev recipe-scraper object dict

        title = meal["title"]
        if info["type"] == "combo_main":
            title = f"Main: {title}"
        elif info["type"] == "combo_side":
            title = f"Side: {title}"
        title = '\t\t<div class="card">\n' f"\t\t\t<h1>{title}</h1>\n"

        try:
            servings = f'\t\t\t<i>{meal["yields"]}'
        except KeyError:
            servings = "\t\t\t<i>servings unknown"

        host = f' | {meal["site_name"]}</i>'

        title_servings = title + servings + host

        image = (
            '<div class="polaroid">\n'
            f'\t\t\t\t<img src={meal["image"]} alt="{meal["title"]} from {meal["host"]}" />\n'
            "\t\t\t</div>"
        )

        ingredients = ["\t\t\t\t<li>" + i + "</li>" for i in meal["ingredients"]]
        ingredients = "\n".join(ingredients)
        ingredients = (
            "\t\t\t<h2>Ingredients</h2>\n" f"\t\t\t<ul>\n{ingredients}\n\t\t\t</ul>"
        )

        instructions = (
            "\t\t\t<h2>Instructions</h2>\n"
            f'\t\t\t<p>{meal["instructions"]}</p>\n\t\t</div>\n'
        )

        container = "\n".join([title_servings, image, ingredients, instructions])
        html = html + container

    # some logic to handle calculating and displaying elapsed time
    elapsed_time = time.time() - start
    if elapsed_time > 1:
        elapsed_time = f"{elapsed_time:.2f} seconds"  # as time in seconds
    else:
        elapsed_time = (
            # convert from seconds to milliseconds
            f"{elapsed_time * 1000:.0f}ms"
        )

    pretty = (
        f"{html}"
        f'\t\t<p style="color: #888;text-align: center;">Wowza! We found '
        f"{unused_main_count + unused_side_count} recipes! "
        f"These {len(meals)} were "
        f"selected at random for your convenience and your family's delight. "
        f"It took {elapsed_time} to do this using v{VERSION}."
        f"</p>\n</body>\n</html>"
    )
    return pretty