import csv
import requests
import json
from django.core.cache import caches


def read_json_file(name):
    print("Reading %s" % name)
    with open(name, "r") as f:
        return json.loads(f.read())

def read_csv_file(name):
    print("Reading %s" % name)
    with open(name, "r") as f:
        reader = csv.DictReader(f)
        return [r for r in reader]

def perc(num, total):
    return num*100.0/total


def get_key(item, keys):
    return "".join([item[k] for k in keys])

def uniqify_list(lst, keys):
    s = {}
    for l in lst:
        s[get_key(l, keys)] = l
    return s.values()

def get_pmg_api_cache():
    return caches["pmg_api"]

cache = get_pmg_api_cache()

def fetch_if_not_in_cache(url):
    if cache.get(url):
        return cache.get(url)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()