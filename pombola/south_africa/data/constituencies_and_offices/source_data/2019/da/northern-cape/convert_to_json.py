import csv
import json
from collections import defaultdict

PROVINCE = "Northern Cape"
PROVINCE_SLUG = "northern-cape"
SOURCE_URL = "https://docs.google.com/spreadsheets/d/1paQJas-FsvCLr49VHD_Lv5WFtgkzCpkN/edit#gid=931115090"
PARTY = "DA"

json_output = {"offices": [], "start_date": "2019-06-01", "end_date": "2019-05-31"}
offices = defaultdict(list)

with open("{}-raw.csv".format(PROVINCE_SLUG)) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        offices[row["Constituency"].strip()].append(row)

for title, office in offices.items():
    json_office = {
        "Title": "{} Constituency Area: {}".format(PARTY, title.strip()),
        "Source URL": SOURCE_URL,
        "Party": PARTY,
        "Type": "area",
        "Source Note": "{} Parliamentary Caucus 2019".format(PARTY),
        "Province": PROVINCE,
        "People": [],
        "Location": title.strip(),
    }
    for person in office:
        position = {"Name": person["Name"].strip()}
        json_office["People"].append(position)
    json_output["offices"].append(json_office)


with open("{}.json".format(PROVINCE_SLUG), "w") as output:
    json.dump(json_output, output, indent=4)
