import pandas as pd

from cook import load_json

# from lists import veggies

df = pd.read_pickle("master_data.pkl")
failures = load_json("failed_recipes.json")
df["fails"] = False
print(df.fails)
for index, row in df.iterrows():
    for failure, reason in failures.items():
        if failure == row["canonical_url"]:
            df.at[index, "fails"] = True
            df.at[index, "fail_reason"] = reason
            print("fails")
            break

"""seafood = "scallops salmon shrimp tuna"
seafood = seafood.split(" ")
landfood = "chickpea chicken turkey pork tofu garbanzo"
landfood = landfood.split(" ")

for index, row in df.iterrows():
    for ingredient in row["ingredients"]:
        if any(food in ingredient.lower() for food in seafood):
            df.at[index, "protein_type"] = "seafood"
            print("found seafood")
            break

        elif any(food in ingredient.lower() for food in landfood):
            df.at[index, "protein_type"] = "landfood"
            print("found landfood")
            break

    for ingredient in row["ingredients"]:
        if any(veggie in ingredient.lower() for veggie in veggies):
            df.at[index, "has_veggies"] = True
            print("True")
            break

        else:
            df.at[index, "has_veggies"] = False
            print("False")
            break
"""
df.to_csv("csv.csv")
df.to_pickle("master_data.pkl")
print(df["fails"])
