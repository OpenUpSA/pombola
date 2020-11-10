import csv
import json

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