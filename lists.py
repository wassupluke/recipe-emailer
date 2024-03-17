# CONSTANTS
# Info about how to process scraping recipe links each site
# source_list format is as follows (by index):
# 0 - html attribute to locate recipies on site
# 1 - html text to match for attribute 0
# 2 - address for main course
# 3 - address for side dishes
# 4 - address for spider (not yet implemented)

# --------------------------------------------------------------------------- #

'''
Currently runs the following websites:

reciperunner.com
paleorunningmomma.com
skinnytaste.com
twopeasandtheirpod.com
wellplated.com
thespruceeats.com
nourishedbynutrition.com
eatingbirdfood.com
budgetbytes.com
leanandgreenrecipes.net
minimalistbaker.com
gimmesomeoven.com
pinchofyum.com
heatherchristo.com
fitslowcookerqueen.com
eatliverun.com
'''

# --------------------------------------------------------------------------- #

full = [
    [
        'a class',
        'wpp-post-title',
        'https://www.reciperunner.com/category/recipes/dinners/',
        'https://reciperunner.com/category/recipes/side-dishes/',
        'https://reciperunner.com/category/recipes/',
    ],
    [
        'a class',
        'entry-title-link',
        'https://www.paleorunningmomma.com/course/dinner/',
        'https://www.paleorunningmomma.com/course/veggies-sides/',
        'https://www.paleorunningmomma.com/course/',
    ],
    [
        'h2 class',
        'entry-title',
        'https://www.skinnytaste.com/?_course=dinner-recipes',
        'https://www.skinnytaste.com/recipes/side-dishes/',
        'https://www.skinnytaste.com/recipes',
    ],
    [
        'h3 class',
        'entry-title',
        'https://www.skinnytaste.com/recipes/dinner-recipes/',
        'https://www.skinnytaste.com/recipes/side-dishes/',
        'https://www.skinnytaste.com/recipes/',
    ],
    [
        'h2 class',
        'post-summary__title',
        'https://www.twopeasandtheirpod.com/category/recipes/main-dishes/',
        'https://www.twopeasandtheirpod.com/category/recipes/side/',
        'https://www.twopeasandtheirpod.com/category/recipes/',
    ],
    [
        'h3 class',
        'post-summary__title',
        'https://www.wellplated.com/category/recipes-by-type/entreesmain-dishes/#recent',
        'https://www.wellplated.com/category/recipes-by-type/side-dishes-recipe-type/#recent',
        'https://www.wellplated.com/category/recipes-by-type/',
    ],
    [
        'a class',
        'comp mntl-card-list-items mntl-document-card mntl-card card card--no-image',
        'https://www.thespruceeats.com/dinner-4162806',
        'https://www.thespruceeats.com/side-dishes-4162722',
        'https://www.thespruceeats.com/',
    ],
    [
        'a class',
        'post',
        'https://nourishedbynutrition.com/recipe-index/?_sft_category=entrees',
        'https://nourishedbynutrition.com/category/recipes/sides/',
        'https://nourishedbynutrition.com/category/recipes/',
    ],
    [
        'h2 class',
        'post-summary__title',
        'https://www.eatingbirdfood.com/category/meal-type/dinnerlunch/',
        'https://www.eatingbirdfood.com/category/meal-type/dinnerlunch/sides/',
        'https://www.eatingbirdfood.com/category/meal-type/',
    ],
    [
        'parent class',
        'post-summary post-summary--secondary',
        'https://www.budgetbytes.com/category/recipes/?fwp_by_course=main-dish',
        'https://www.budgetbytes.com/category/recipes/side-dish/',
        'https://www.budgetbytes.com/category/recipes/',
    ],
    [
        'h2 class',
        'recipe-card-title',
        'https://www.leanandgreenrecipes.net/recipes/category/main-course/',
        'https://www.leanandgreenrecipes.net/recipes/category/accompaniment/',
        'https://www.leanandgreenrecipes.net/recipes/category/',
    ],
    [
        'h3 class',
        'post-summary__title',
        'https://www.minimalistbaker.com/recipe-index/?fwp_recipe-type=entree',
        'https://www.minimalistbaker.com/recipe-index/?fwp_recipe-type=salad',
        'https://www.minimalistbaker.com/recipe-index/',
    ],
    [
        'div class',
        'teaser-post-sm',
        'https://www.gimmesomeoven.com/all-recipes/?fwp_course=main-course',
        'https://www.gimmesomeoven.com/all-recipes/?fwp_course=side-dishes',
        'https://www.gimmesomeoven.com/all-recipes/',
    ],
    [
        'h2 class',
        'post-summary__title',
        'https://www.halfbakedharvest.com/category/recipes/type-of-meal/main-course/',
        'https://www.halfbakedharvest.com/category/recipes/type-of-meal/side-dishesvegetables/',
        'https://halfbakedharvest.com/',
    ],
    [
        'a class',
        'block md:hover:opacity-60 space-y-2 flex flex-col',
        'https://pinchofyum.com/recipes/dinner',
        'https://pinchofyum.com/recipes/salad',
        ],
    [
        'div class',
        'feature-title-wrapper',
        'https://heatherchristo.com/category/recipes/?cat=10533&orderby=date',
        'https://heatherchristo.com/category/recipes/?cat=200&orderby=date',
        ],
    [
        'a class',
        'excerpt-link',
        'https://fitslowcookerqueen.com/category/slowcooker/',
        'https://fitslowcookerqueen.com/category/salads/',
        ],
    [
        'div class',
        'post-img',
        'https://www.eatliverun.com/category/recipes-2/main-course-2/',
        'https://www.eatliverun.com/category/recipes-2/side-dishes/',
        ],
]

# short list for debugging
debug = []

# a list of key veggies that we want in a meal
veggie_list = [
    'acorn aquash',
    'artichoke',
    'arugula',
    'asparagus',
    'bell pepper',
    'broccoli',
    'broccolini',
    'brussel sprouts',
    'butternut squash',
    'cabbage',
    'carrot',
    'cannellini',
    'cauliflower',
    'celery',
    'cucumber',
    'eggplant',
    'garbanzo',
    'green bean',
    'kale',
    'kohlrabi',
    'lettuce',
    'mushroom',
    'nori',
    'ogonori',
    'okra',
    'peas',
    'potato',
    'radish',
    'snap pea',
    'soybean',
    'spinach',
    'squash',
    'yam',
    'zucchini',
]
