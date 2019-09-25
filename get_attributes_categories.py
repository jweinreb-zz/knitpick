import os
import pandas as pd
import requests

auth = requests.auth.HTTPBasicAuth(
    os.getenv("RAVELRY_KEY"), os.getenv("RAVELRY_SECRET")
)

## Pattern attributes - tags, to add as columns in pattern database
patt_attrs = requests.get(
    "https://api.ravelry.com/pattern_attributes/groups.json", auth=auth
)
patt_attrs = [grp for grp in patt_attrs.json()["attribute_groups"]]
records = []
for cat in patt_attrs:
    for a in cat.get("pattern_attributes"):
        records.append(a)
    children = cat["children"]
    if children:
        for child in children:
            for a2 in child.get("pattern_attributes"):
                records.append(a2)
            childdren = child["children"]
            if childdren:
                for childd in childdren:
                    for a3 in childd.get("pattern_attributes"):
                        records.append(a3)

attributes = pd.DataFrame.from_records(records)[["id", "name", "description"]]

if __name__ == "__main__":
    print(attributes.head())


## Pattern Categories - types of patterns to scrape
patt_cats = requests.get(
    "https://api.ravelry.com/pattern_categories/list.json", auth=auth
)
patt_cats = patt_cats.json()["pattern_categories"]["children"]
accessories_and_clothing = [patt_cats[0]] + [patt_cats[1]]

records = []
for cat in accessories_and_clothing:
    record = {k: v for k, v in cat.items() if k in ["id", "long_name"]}
    records.append(record)
    children = cat["children"]
    if children:
        for child in children:
            record = {k: v for k, v in child.items() if k in ["id", "long_name"]}
            records.append(record)
            childdren = child["children"]
            if childdren:
                for childd in childdren:
                    record = {
                        k: v for k, v in childd.items() if k in ["id", "long_name"]
                    }
                    records.append(record)
categories = pd.DataFrame.from_records(records)

if __name__ == "__main__":
    print(categories.head())
