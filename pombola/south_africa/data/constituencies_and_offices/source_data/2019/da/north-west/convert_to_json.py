import csv
import json
from collections import defaultdict

json_output = {"offices": [], "start_date": "2019-06-01", "end_date": "2019-05-31"}

offices = defaultdict(list)

with open("north-west-raw.csv") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row["Within constituency"].strip():
            offices[row["Within constituency"].strip()].append(row)
        elif row["Head of constituency"].strip():
            offices[row["Head of constituency"].strip()].append(row)

for title, office in offices.items():
    json_office = {
        "Title": "DA Constituency Area: %s" % title.strip(),
        "Source URL": "https://www.pa.org.za/media_root/file_archive/Copy_of_NW_MP-L_Dermacation_List.xlsx",
        "Party": "DA",
        "Type": "area",
        "Source Note": "DA Parliamentary Caucus 2019",
        "Province": "North West",
        "People": [],
        "Location": title.strip(),
    }
    for person in office:
        position = {
            "Cell": person["Cellphone"].strip(),
            "Email": person["Public email"].strip(),
            "Name": "%s %s"
            % (person["First names"].strip(), person["Last name"].strip()),
        }
        if person["Head of constituency"].strip():
            position["Position"] = "Constituency Head"
        json_office["People"].append(position)
    json_output["offices"].append(json_office)


with open("north-west.json", "w") as output:
    json.dump(json_output, output, indent=4)
