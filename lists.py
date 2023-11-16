# CONSTANTS
# Info about how to process scraping recipe links each site
# sites_to_scrape format is as follows (by index):
# 0 - html attribute to locate recipies on site
# 1 - site address for main course
# 2 - html text to match for attribute 0
# 3 - site address for side dishes
full = [
    [
        "a class",
        "https://www.reciperunner.com/category/recipes/dinners/",
        "wpp-post-title",
        "https://reciperunner.com/category/recipes/side-dishes/",
    ],
    [
        "a class",
        "https://www.paleorunningmomma.com/course/dinner/",
        "entry-title-link",
        "https://www.paleorunningmomma.com/course/veggies-sides/",
    ],
    [
        "h2 class",
        "https://www.skinnytaste.com/?_course=dinner-recipes",
        "entry-title",
        "https://www.skinnytaste.com/recipes/side-dishes/",
    ],
    [
        "h3 class",
        "https://www.skinnytaste.com/recipes/dinner-recipes/",
        "entry-title",
        "https://www.skinnytaste.com/recipes/side-dishes/",
    ],
    [
        "h2 class",
        "https://www.twopeasandtheirpod.com/category/recipes/main-dishes/",
        "post-summary__title",
        "https://www.twopeasandtheirpod.com/category/recipes/side/",
    ],
    [
        "h3 class",
        "https://www.wellplated.com/category/recipes-by-type/\
                entreesmain-dishes/#recent",
        "post-summary__title",
        "https://www.wellplated.com/category/recipes-by-type/\
                side-dishes-recipe-type/#recent",
    ],
    [
        "a class",
        "https://www.thespruceeats.com/dinner-4162806",
        "comp mntl-card-list-items mntl-document-card mntl-card \
                card card--no-image",
        "https://www.thespruceeats.com/side-dishes-4162722",
    ],
    [
        "a class",
        "https://nourishedbynutrition.com/recipe-index/\
                ?_sft_category=entrees",
        "post",
        "https://nourishedbynutrition.com/category/recipes/sides/",
    ],
    [
        "h2 class",
        "https://www.eatingbirdfood.com/category/meal-type/dinnerlunch/",
        "post-summary__title",
        "https://www.eatingbirdfood.com/category/meal-type/dinnerlunch/sides/",
    ],
    [
        "parent class",
        "https://www.budgetbytes.com/category/recipes/\
                ?fwp_by_course=main-dish",
        "post-summary post-summary--secondary",
        "https://www.budgetbytes.com/category/recipes/side-dish/",
    ],
    [
        "h2 class",
        "https://leanandgreenrecipes.net/recipes/category/main-course/",
        "recipe-card-title",
        "https://leanandgreenrecipes.net/recipes/category/accompaniment/",
    ],
    [
        "h3 class",
        "https://minimalistbaker.com/recipe-index/?fwp_recipe-type=entree",
        "post-summary__title",
        "https://minimalistbaker.com/recipe-index/?fwp_recipe-type=salad",
    ],
    [
        "div class",
        "https://www.gimmesomeoven.com/all-recipes/?fwp_course=main-course",
        "teaser-post-sm",
        "https://www.gimmesomeoven.com/all-recipes/?fwp_course=side-dishes",
    ]
]

# short list for debugging
debug = [
    [
        "div class",
        "https://www.gimmesomeoven.com/all-recipes/?fwp_course=main-course",
        "teaser-post-sm",
        "https://www.gimmesomeoven.com/all-recipes/?fwp_course=side-dishes",
    ]
]

# a list of key veggies that we want in a meal
veggie_list = [
    "acorn aquash",
    "artichoke",
    "arugula",
    "asparagus",
    "bell pepper",
    "broccoli",
    "broccolini",
    "brussel sprouts",
    "butternut squash",
    "cabbage",
    "carrot",
    "cannellini",
    "cauliflower",
    "celery",
    "cucumber",
    "eggplant",
    "garbanzo",
    "green bean",
    "kale",
    "kohlrabi",
    "lettuce",
    "mushroom",
    "nori",
    "ogonori",
    "okra",
    "peas",
    "potato",
    "radish",
    "snap pea",
    "soybean",
    "spinach",
    "squash",
    "yam",
    "zucchini",
]
