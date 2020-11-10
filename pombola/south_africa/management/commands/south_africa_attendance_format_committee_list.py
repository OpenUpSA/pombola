import csv
import json
import operator
import re

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from haystack.inputs import AutoQuery, Raw
from haystack.query import SearchQuerySet
from pombola.core.models import Organisation, OrganisationKind

# TODO: filter out those without meetings
# TODO: find PA committees by name

# TODO: out:
# pmg_id, pmg_name, pmg_house, pa_matches: { pa_id, pa_name, pa_house }

# In:
# id_pmg	num_meetings	remarks	match_confirmed	name_pmg	house_pmg	pa_name_0	pa_house_0	pa_link_0	pa_name_1	pa_house_1	pa_link_1	pa_name_2	pa_house_2	pa_link_2	pa_name_3	pa_house_3	pa_link_3

IN_FILE = "pmg-attendance/pmg-pa-committees-checked.csv"
OUT_FILE = "pmg-attendance/pmg-pa-committee-matches.json"

def read_in_file():
    print("Reading %s" % IN_FILE)
    with open(IN_FILE, 'r') as f:
        reader = csv.DictReader(f)
        data = []
        for row in reader:
            data.append(row)
        
    return data

def find_pa_comm(name, house, url):
    n = url[:url.rindex('/')]
    com_id = int(n[n.rindex('/')+1:])
    return Organisation.objects.get(
        id=com_id,
    )

def transform_to_out_com(com):
    # pmg_id, pmg_name, pmg_house, pa_matches: { pa_id, pa_name, pa_house }
    d = {
        'pmg_id': com['id_pmg'],
        'pmg_name': com['name_pmg'],
        'pmg_house': com['house_pmg'],
        'houses': [],
    }
    for i in range(4):
        pa_name = com["pa_name_%d" % i].strip()
        pa_house = com["pa_house_%d" % i].strip()
        pa_link = com["pa_link_%d" % i].strip()
        print("Finding %s" % pa_name)
        if pa_name:
            pa_com = find_pa_comm(pa_name, pa_house, pa_link)
            d['houses'].append({
                'pa_id': pa_com.id,
                'pa_name': pa_name,
                'pa_house': pa_com.kind.name
            })
    return d

def write_to_out_file(data):
    print("Writing to %s" % OUT_FILE)
    with open(OUT_FILE, 'w') as f:
        f.write(json.dumps(data, indent=4))



class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        data = read_in_file()
        with_meetings = [d for d in data if d['num_meetings'] > 0]
        out_data = []
        for com in with_meetings:
            out_data.append(transform_to_out_com(com))
        
        write_to_out_file(out_data)

