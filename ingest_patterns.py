from flask import Flask, request
import operator
from functools import reduce

# from flask_restful import Resource, Api, reqparse
import requests
import os
import pandas as pd
import re
import logging
import pickle
import datetime as dt
import psycopg2

formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")


def setup_logger(name, log_file, level=logging.INFO):
    """Function setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def clean_attribute_text(attribute: str):
    """ Standardize attribute names"""
    att1 = attribute.lower().split(" (")[0].strip()
    att2 = (
        att1.replace(" - ", "_").replace("-", "_").replace(" / ", "_").replace("/", "_")
    )
    att3 = att2.replace(" ", "_").replace("'", "")
    rgx = re.search(r"^.+?(?=\_+$)", att3)
    att4 = rgx.group(0) if rgx else att3
    return att4


PATTERN_ATTRIBUTES = pd.read_csv("pattern_attributes.csv")
PATTERN_ATTRIBUTES.loc[:, "name"] = PATTERN_ATTRIBUTES.name.apply(
    lambda x: clean_attribute_text(x)
)
PATTERN_ATTRIBUTES = PATTERN_ATTRIBUTES.drop_duplicates(subset="name")

NEEDLES = pd.read_csv("needle_sizes.csv")
NEEDLES.loc[:, "us"] = NEEDLES.us.apply(
    lambda x: str(x).replace("/", "s").replace(".5", "h")
    if ("/" in str(x)) or (".5" in str(x))
    else str(x.split(".")[0])
)


logging.basicConfig(level=logging.INFO, filename="out.text")
logger = logging.getLogger()

RAVELRY_KEY = os.getenv("RAVELRY_KEY")
RAVELRY_SECRET = os.getenv("RAVELRY_SECRET")
auth = requests.auth.HTTPBasicAuth(RAVELRY_KEY, RAVELRY_SECRET)

# API endpoint and requests
ENDPOINT = "https://api.ravelry.com"
SEARCH_PATTERNS_URL = (
    ENDPOINT + "/patterns/search.json?craft=knitting&pc=%s"
)  # Get patterns for a category
SEARCH_PATTERNS_URL_PAGE = (
    ENDPOINT + "/patterns/search.json?craft=knitting&pc=%s&page=%d"
)  # Get specific page # of pattern search results
LIST_PATTERN_PROJECTS_URL = (
    ENDPOINT + "/patterns/%d/projects.json"
)  # Get projects for a pattern
SINGLE_PATTERN_DETAIL_URL = (
    ENDPOINT + "/patterns/%d.json"
)  # Get details for a single pattern
MULTIPLE_PATTERN_DETAIL_URL = (
    ENDPOINT + "/patterns.json?ids=%s"
)  # ints separated by +, i.e. 600+818
LIST_USER_PROJECTS_URL = (
    ENDPOINT + "/projects/%s/list.json"
)  # Get a user's project list
USER_INFO_URL = ENDPOINT + "/people/%d.json"  # Get a user's profile info

# psql conn
CONN_DICT = {
    "host": "localhost",
    "dbname": "insight",
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
}

## pattern categories
categories = [
    "pullover",
    "cardigan",
    "other-sweater",
    "coat",
    "dress",
    "shrug",
    "skirt",
    "vest",
    "tee",
    "sleeveless-top",
    "strapless-top",
    "other-top",
    "ankle",
    "knee-highs",
    "mid-calf",
    "thigh-high",
    "toeless",
    "tube",
    "other-socks",
    "scarf",
    "cowl",
    "shawl-wrap",
    "fingerless",
    "gloves",
    "mittens",
    "hat",
]

## pattern metadata
orig_patt_keys = [
    "published",
    "name",
    "permalink",
    "url",
    "difficulty_average",
    "difficulty_count",
    "rating_average",
    "comments_count",
    "rating_count",
    "favorites_count",
    "projects_count",
    "queued_projects_count",
    "free",
    "price",
    "currency",
    "generally_available",
    "ravelry_download",
    "downloadable",
    "yardage_max",
]

needles_cols = ["needles_us_" + s for s in NEEDLES.us]

features_cols = ["attribute_" + a for a in PATTERN_ATTRIBUTES.name]


def get_pattern_data_by_id(pattern_id: int) -> dict:
    """ Retrieve API record for single pattern given its id"""
    resp = requests.get(SINGLE_PATTERN_DETAIL_URL % pattern_id, auth=auth)
    if resp.ok:
        return resp.json()["pattern"]
    else:
        logger.error("Pattern with id %d does not exist" % pattern_id)
        return None


def parse_pattern(pattern_data: dict) -> dict or None:
    """Transform pattern record from API to standardized form for ingestion"""
    patt_info = {k: v for k, v in pattern_data.items() if k in orig_patt_keys}
    patt_info["name"] = pattern_data["name"].strip()
    patt_info["pattern_id"] = pattern_data["id"]
    patt_info["num_photos"] = 0
    if pattern_data.get("photos"):
        patt_info["num_photos"] = len(pattern_data.get("photos"))

    if patt_info["generally_available"]:
        patt_info["generally_available"] = dt.datetime.strftime(
            pd.to_datetime(pattern_data["generally_available"]), "%Y-%m-%d"
        )
    if patt_info["published"]:
        patt_info["published"] = dt.datetime.strftime(
            pd.to_datetime(pattern_data["published"]), "%Y-%m-%d"
        )
    # pattern author info
    patt_info["author_name"] = pattern_data["pattern_author"]["name"].strip()
    patt_info["author_pattern_count"] = pattern_data["pattern_author"][
        "knitting_pattern_count"
    ]
    patt_info["author_favorites_count"] = pattern_data["pattern_author"][
        "favorites_count"
    ]
    patt_info["author_id"] = pattern_data["pattern_author"]["id"]

    # yarn data
    patt_info["yardage_min"] = pattern_data["yardage"]
    if pattern_data.get("yarn_weight"):  # may be None
        patt_info["yarn_weight"] = pattern_data.get("yarn_weight")["name"]
    else:
        patt_info["yarn_weight"] = None

    # row gauge
    gauge_divisor = (
        pattern_data["gauge_divisor"] if pattern_data["gauge_divisor"] else 4
    )
    if pattern_data.get("row_gauge"):
        patt_info["row_gauge"] = pattern_data["row_gauge"] / gauge_divisor
    else:
        patt_info["row_gauge"] = None

    # stitch gauge
    if pattern_data["gauge"]:
        patt_info["stitch_gauge"] = pattern_data["gauge"] / gauge_divisor
    else:
        patt_info["stitch_gauge"] = None

    # add pattern attribute columns
    for ftr in features_cols:
        patt_info[ftr] = False
    for a in pattern_data["pattern_attributes"]:
        # have to link by ids due to naming inconsistency in search and features API
        attr_name = PATTERN_ATTRIBUTES["name"][PATTERN_ATTRIBUTES.id == a["id"]]
        if not attr_name.empty:
            attr_name = attr_name.values[0]
            patt_info["attribute_" + attr_name] = True

    # needle data
    for needle in needles_cols:
        patt_info[needle] = False
    for ns in pattern_data["pattern_needle_sizes"]:
        if ns["us"] is not None:
            # US patterns and sizes only:
            needle_name = NEEDLES["us"][NEEDLES.id == ns["id"]].values[0]
            patt_info["needles_us_" + needle_name] = True

    return patt_info


def get_pattern_info_by_id(patt_id: int):
    """ Given pattern id, get standardized entry for database insert"""
    patt_data = get_pattern_data_by_id(patt_id)
    patt_info = parse_pattern(patt_data)
    return patt_info


def get_pattern_records_in_category(category: str) -> list:
    """ Return list of standard pattern records, one for each pattern in specified category """
    # Number of pages and number of results for each category of pattern
    paginator = requests.get(SEARCH_PATTERNS_URL % category, auth=auth).json()[
        "paginator"
    ]
    n_pages, n_patterns = paginator["page_count"], paginator["results"]
    logger.info(
        "Found %d %s patterns, %d pages total" % (n_patterns, category, n_pages)
    )
    # For each page of search results:
    records = []
    for i in range(n_pages):
        logger.info("Getting page %d of %d" % (i + 1, n_pages + 1))
        # Get pattern ids of each page joined in + concatenated list
        resp = requests.get(
            SEARCH_PATTERNS_URL_PAGE % (category, i + 1), auth=auth
        ).json()
        patt_ids_suffix = "+".join([str(r["id"]) for r in resp["patterns"]])
        # Get detailed pattern info for these ids in one call:
        resp = requests.get(MULTIPLE_PATTERN_DETAIL_URL % patt_ids_suffix, auth=auth)
        patterns = resp.json()["patterns"]
        for patt_id, patt_data in patterns.items():
            patt_info = parse_pattern(patt_data)
            if patt_info is not None:
                patt_info["category"] = category
                try:
                    records.append(patt_info)
                except:
                    logger.error("Skipping pattern id %d" % patt_id)
    df = pd.DataFrame.from_records(records)
    return df


# 443533 Flax has many projects...
def get_user_ids_by_pattern(pattern_id: int):
    resp = requests.get(LIST_PATTERN_PROJECTS_URL % pattern_id, auth=auth)
    if resp.ok:
        paginator = resp.json()["paginator"]
        n_pages, n_patterns = paginator["page_count"], paginator["results"]
        projects = resp.json()["projects"]
    else:
        logger.debug("Pattern with id %d does not exist" % pattern_id)

    user_ids = []
    for i in range(n_pages):
        logger.info("Getting page %d of %d" % (i + 1, n_pages + 1))
        if i > 0:
            resp = requests.get(
                (ingest_patterns.LIST_PATTERN_PROJECTS_URL % pattern_id)
                + ("/?page=%s" % str(i + 1)),
                auth=ingest_patterns.auth,
            )
        projects = resp.json()["projects"]
        user_ids.extend([p["user_id"] for p in projects])

    return user_ids


def insert_pattern_info_in_db(
    patt_info: dict,
    conn_dict: dict = CONN_DICT,
    db_name: str = "insight",
    table_name: str = "patterns",
):
    with psycopg2.connect(**CONN_DICT) as conn, conn.cursor() as cur:
        query = "INSERT INTO patterns3({}) VALUES ({});".format(
            ", ".join(list(patt_info.keys())),
            ", ".join([f"%({k})s" for k in list(patt_info.keys())]),
        )
        cur.execute(query, patt_info)


def insert_pattern_id_in_db(patt_id: int):
    patt_data = get_pattern_data_by_id(patt_id)
    if patt_data is not None:
        try:
            patt_info = parse_pattern(patt_data)
        except:
            logger.error(f"Error parsing pattern {patt_id}")
        if patt_info is not None:
            try:
                insert_pattern_info_in_db(patt_info)
            except:
                logger.error(f"Error inserting pattern_info from id {patt_id}")
    else:
        logger.info(f"Skipping pattern id {patt_id} because pattern DNE")


def insert_pattern_records_in_category(category: str) -> list:
    """ Insert records into sqldb, one for each pattern in specified category """
    # Number of pages and number of results for each category of pattern
    paginator = requests.get(SEARCH_PATTERNS_URL % category, auth=auth).json()[
        "paginator"
    ]
    n_pages, n_patterns = paginator["page_count"], paginator["results"]
    logger.info(
        "Found %d %s patterns, %d pages total" % (n_patterns, category, n_pages)
    )
    # For each page of search results:
    records = []
    for i in range(n_pages):
        logger.info("Getting page %d of %d" % (i + 1, n_pages + 1))
        # Get pattern ids of each page joined in + concatenated list
        resp = requests.get(
            SEARCH_PATTERNS_URL_PAGE % (category, i + 1), auth=auth
        ).json()
        patt_ids_suffix = "+".join([str(r["id"]) for r in resp["patterns"]])
        # Get detailed pattern info for these ids in one call:
        resp = requests.get(MULTIPLE_PATTERN_DETAIL_URL % patt_ids_suffix, auth=auth)
        try:
            patterns = resp.json()["patterns"]
            for j, (patt_id, patt_data) in enumerate(patterns.items()):
                patt_info = parse_pattern(patt_data)
                if patt_info is not None:
                    patt_info["pattern_type"] = category
                    # logger.info(f'Inserting pattern_id {patt_id}')
                    try:
                        insert_pattern_info_in_db(patt_info)
                    except:
                        logger.error(
                            f"Pattern {patt_id} does not have US needles; skipping"
                        )
        except Exception as e:
            logger.error(f"Error inserting page {i+1} of category {e}")


table_query_base = """CREATE TABLE patterns3(name text, permalink text, price numeric, projects_count int,
                 published date, queued_projects_count int, rating_average numeric, rating_count int,
                 url text, comments_count int, currency text, difficulty_average numeric, difficulty_count int,
                 downloadable boolean, favorites_count int, free boolean, generally_available date, 
                 yardage_max int, ravelry_download boolean, pattern_id bigint, pattern_type text,
                 author_name text, author_pattern_count int, author_favorites_count int, author_id bigint,
                 yardage_min int, yarn_weight text, row_gauge numeric, stitch_gauge numeric, num_photos int, """


table_query = (
    table_query_base
    + ", ".join([x + " boolean" for x in needles_cols + features_cols])
    + ");"
)


if __name__ == "__main__":
    categories = [
        "cardigan",
        "other-sweater",
        "coat",
        "dress",
        "shrug",
        "skirt",
        "vest",
    ]
    # Cardigan JSONDecode error in line 259 patterns = resp.json()['patterns']

    for category in categories:
        logger = setup_logger(category, f"third_{category}.log")
        insert_pattern_records_in_category(category)
