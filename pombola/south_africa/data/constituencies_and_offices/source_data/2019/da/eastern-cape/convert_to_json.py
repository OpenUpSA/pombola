import csv
import json
from collections import defaultdict

PROVINCE = "Eastern Cape"
PROVINCE_SLUG = "eastern-cape"
SOURCE_URL = "https://www.pa.org.za/media_root/file_archive/Copy_of_Copy_of_Constituency_Administrators_Eastern_Cape_-_June_2019.xlsx"
PARTY = "DA"

json_output = {"offices": [], "start_date": "2019-06-01", "end_date": "2019-05-31"}
offices = defaultdict(list)

with open("{}-raw.csv".format(PROVINCE_SLUG)) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        title = row["Constituency"]
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
        leader = {
            "Name": row["Constituency Leader"].strip(),
            "Position": "Constituency Leader"
        }
        administrator = {
            "Name": row["Administrators"].strip(),
            "Position": "Administrator"
        }
        json_office["People"].append(leader)
        json_office["People"].append(administrator)
        json_output["offices"].append(json_office)


with open("{}.json".format(PROVINCE_SLUG), "w") as output:
    json.dump(json_output, output, indent=4)
