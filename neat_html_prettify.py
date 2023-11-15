from css import head

def prettify_neat(m, ar, x):
    '''Function converts meal object info into HTML for email'''
    title = m.title()
    if x == 0:
        title = f"Main: {title}"
    elif x == 1:
        title = f"Side: {title}"
    else:
        pass
    title = f"<section><h1>{title}</h1>"
    try:
        servings = f"<i style=margin-top:0;color:gray>{m.yields()}</i>"
    except SchemaOrgException:
        servings = "<i>servings unknown</i>"
    title_servings = title + servings
    ingredients = ["<li>" + i + "</li>" for i in m.ingredients()]
    ingredients = "\n".join(ingredients)
    ingredients = f"<h3>Ingredients</h3><ul>{ingredients}</ul>"
    instructions = m.instructions()
    instructions = f"<h3>Instructions</h3>\n<p>{instructions}</p></section>"
    r = [title_servings, ingredients, instructions]
    full_recipe = "\n\n".join(r)
    ar.append(full_recipe)
    return ar

pretty = "\n\n".join(all_recipes)
total_sites_line = (
            f'<p style="color: #888;">Wowza! We found '
            f"{len(recipebook) + len(scraperbook)} recipes! "
            f"These {len(meals)} were selected at random for "
            f"your convenience and your family's delight. "
            f"It took {(time.time() - start):.2f} seconds to do "
            f"it using v10</p>"
            )
prettiest = f"{head}<body>{pretty}\n\n{total_sites_line}</body></html>"

