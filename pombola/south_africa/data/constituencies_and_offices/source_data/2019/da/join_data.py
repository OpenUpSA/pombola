import csv
import json
from collections import defaultdict

PROVINCE = "Limpopo"
PROVINCE_SLUG = "limpopo"
SOURCE_URL = "https://www.pa.org.za/media_root/file_archive/Limpopo_Public_Rep_list.xlsx"
PARTY = "DA"

json_output = {"offices": [], "start_date": "2019-06-01", "end_date": "2019-05-31"}

input_files = [
    './eastern-cape/eastern-cape.json',
    './free-state/freestate.json',
    './gauteng/gauteng.json',
    './kzn/kwazulu-natal.json',
    './limpopo/limpopo.json',
    './mpumalanga/mpumalanga.json',
    './north-west/north-west.json',
    './northern-cape/northern-cape.json',
    './western-cape/western-cape.json',
]

offices_count = 0

for input_file in input_files:
    with open(input_file) as csvfile:
        data = csvfile.read()

    json_data = json.loads(data)
    json_output["offices"] += json_data['offices']
    offices_count += len(json_data['offices'])

with open("all-provinces.json".format(PROVINCE_SLUG), "w") as output:
    json.dump(json_output, output, indent=4)

print("Total offices count: {}".format(offices_count))
print("Offices len in json: {}".format(len(json_output['offices'])))

