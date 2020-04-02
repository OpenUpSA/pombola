import csv
import json
from collections import defaultdict

PROVINCE = "KwaZulu-Natal"
PROVINCE_SLUG = "kwazulu-natal"
SOURCE_URL = "https://docs.google.com/spreadsheets/d/1nGO_kx1sa3UWG4nB1cOD5ppu7dOXBpQK/edit#gid=1842508354"
PARTY = "DA"

json_output = {"offices": [], "start_date": "2019-06-01", "end_date": "2019-05-31"}
offices = defaultdict(list)

with open("kzn-constituency-heads-raw.csv".format(PROVINCE_SLUG)) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        offices[row["CONSTITUENCY"].strip()].append(row)

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
        name_surname = "{} {}".format(person["Name"].strip(), person["Surname"].strip())
        if name_surname != ' ':
            position = {
                "Name": name_surname,
                "Cell": person["Mobile"].strip(),
                "Email": person["Email Address"].strip(),
                "Position": 'Constituency Head',
            }
            json_office["People"].append(position)
    json_output["offices"].append(json_office)


with open("{}.json".format(PROVINCE_SLUG), "w") as output:
    json.dump(json_output, output, indent=4)
