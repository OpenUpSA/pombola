import csv
import json
from collections import defaultdict

json_output = {"offices": [], "start_date": "2019-06-01", "end_date": "2019-05-31"}

offices = defaultdict(list)

with open("mpumalanga-raw.csv") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row["Constituency"].strip():
            offices[row["Constituency"].strip()].append(row)

for title, office in offices.items():
    json_office = {
        "Title": "DA Constituency Area: %s" % title.strip(),
        "Source URL": "https://www.pa.org.za/media_root/file_archive/Mpumalanga.xlsx",
        "Party": "DA",
        "Type": "area",
        "Source Note": "DA Parliamentary Caucus 2019",
        "Province": "Mpumalanga",
        "People": [],
        "Location": title.strip(),
    }
    for person in office:
        json_office["People"].append(
            {"Cell": person["number"].strip(), "Name": person["Full name"].strip()}
        )
    json_output["offices"].append(json_office)


with open("mpumalanga.json", "w") as output:
    json.dump(json_output, output, indent=4)
