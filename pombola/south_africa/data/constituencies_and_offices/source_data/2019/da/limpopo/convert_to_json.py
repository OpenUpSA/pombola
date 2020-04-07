import csv
import json
from collections import defaultdict

PROVINCE = "Limpopo"
PROVINCE_SLUG = "limpopo"
SOURCE_URL = "https://www.pa.org.za/media_root/file_archive/Limpopo_Public_Rep_list.xlsx"
PARTY = "DA"

json_output = {"offices": [], "start_date": "2019-06-01", "end_date": "2019-05-31"}

offices = defaultdict(list)

with open("{}-raw.csv".format(PROVINCE_SLUG)) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row["Assigned Constituency"].strip():
            offices[row["Assigned Constituency"].strip()].append(row)

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
        position = {
            "Cell": person["Cellphone"].strip(),
            "Email": person["Party email"].strip(),
            "Name": "{} {}".format(person["First names"].strip(), person["Last name"].strip()).title(),
            "Position": "Administrator"
        }
        json_office["People"].append(position)
    json_output["offices"].append(json_office)


with open("{}.json".format(PROVINCE_SLUG), "w") as output:
    json.dump(json_output, output, indent=4)
