#!/usr/bin/env python

# Take the json in the file given as first argument and convert it to the JSON
# format needed for import. Should do all cleanup of data and removal of
# unneeded entries too.

import json
import os
import re
import sys

import django
import urllib

from django.db.models import Q
from django.utils.text import slugify

script_dir = os.path.basename(__file__)
base_dir = os.path.join(script_dir, "../../../../..")
app_path = os.path.abspath(base_dir)
sys.path.append(app_path)


settings_module = "pombola.settings.south_africa"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
django.setup()
from pombola.core.models import Person

class Converter(object):

    groupings = []

    ditto_marks = [
        "\"",
        "\" \"",
    ]

    # Change this to True to enable little bits of helper code for finding new
    # slug corrections:
    finding_slug_corrections = True

    parties = ["ACDP", "AIC", "AL JAMA-AH", "ANC", "ATM", "COPE", "DA", "EFF", "FF PLUS", "GOOD", "IFP", "NFP", "PAC", "UDM"]
    unique_case_surname = ["ABRAHAM NTANTISO", "BODLANI MOTSHIDI", "LE GOFF", "MAZZONE MICHAEL", "MC GLUWA", "VAN ZYL", "NTLANGWINI LOUW", "DE BRUYN", "DENNER JORDAAN", "DU TOIT", "VAN STADEN"]

    slug_corrections = {
        # Garbage entries
        "control-flag-ict": None,
    }

    category_sort_orders = {
        "SHARES AND OTHER FINANCIAL INTERESTS": 1,
        "REMUNERATED EMPLOYMENT OR WORK OUTSIDE OF PARLIAMENT": 2,
        "DIRECTORSHIPS AND PARTNERSHIPS": 3,
        "CONSULTANCIES AND RETAINERSHIPS": 4,
        "SPONSORSHIPS": 5,
        "GIFTS AND HOSPITALITY": 6,
        "BENEFITS AND INTERESTS FREE LOANS": 7,
        "TRAVEL": 8,
        "OWNERSHIP IN LAND AND PROPERTY": 9,
        "PENSIONS": 10,
        "RENTED PROPERTY": 11,
        "INCOME GENERATING ASSETS": 12,
        "TRUSTS": 13
    }

    def __init__(self, filename):
        self.filename = filename
        self.mp_count = {}

    def convert(self):
        data = self.extract_data_from_json()

        self.extract_release(data)
        self.extract_entries(data)

        return self.produce_json()

    def extract_release(self, data):
        source_url = data['source']
        year = data['year']
        date = data['date']

        source_filename = re.sub(r'.*/(.*?)\.pdf', r'\1', source_url)
        source_name = urllib.unquote(source_filename).replace('_', ' ').strip()

        self.release = {
            "name": "Parliament Register of Members' Interests " + year,
            "date": date,
            "source_url": source_url,
        }

    def extract_entries(self, data):
        for register_entry in data['register']:
            for raw_category_name, entries in register_entry.items():
                # we only care about entries that are arrays
                if type(entries) != list:
                    continue

                # go through all entries stripping off extra whitespace from
                # keys and values
                for entry in entries:
                    for key in entry.keys():

                        # correct common scraper heading error
                        key_to_use = key.strip()
                        if key_to_use == 'Benefits' and raw_category_name.strip() == "TRUSTS":
                            key_to_use = "Details Of Benefits"

                        entry[key_to_use] = entry.pop(key).strip()

                    if entry.get('No') == 'Nothing to disclose':
                        del entry['No']

                # Need to be smart about values that are just '"' as these are dittos of the previous entries.
                previous_entries = []
                for entry in entries:
                    if len(previous_entries):
                        for key in entry.keys():
                            if entry[key] in self.ditto_marks:
                                for previous in reversed(previous_entries):
                                    if key in previous:
                                        entry[key] = previous[key]
                                        break
                                # Replacement may not have been found, warn
                                # if entry[key] in self.ditto_marks:
                                #     sys.stderr.write("----------- Could not find previous entry for ditto mark of '{0}'\n".format(key))
                                #     sys.stderr.write(str(previous_entries) + "\n")
                                #     sys.stderr.write(str(entry) + "\n")
                    previous_entries.append(entry)

                # Filter out entries that are empty
                entries = [e for e in entries if len(e)]

                if len(entries) == 0:
                    continue

                grouping = {
                    "release": self.release,
                    "entries": entries,
                }

                # Extract the category name we are interested in
                category_name = raw_category_name.strip()
                category_name = re.sub(r'^\d+\.\s*', '', category_name)

                grouping['category'] = {
                    "sort_order": self.category_sort_orders[category_name],
                    "name": category_name,
                }

                # Work out who the person is
                person_slug = self.mp_to_person_slug(register_entry['mp'])
                if not person_slug:
                    continue  # skip if no slug
                self.mp_count[person_slug] = register_entry['mp']
                grouping['person'] = {
                    "slug": person_slug
                }

                self.groupings.append(grouping)
            # break # just for during dev

    def mp_to_person_slug(self, mp):
        # pattern = r'\b(?:{})\b'.format('|'.join(map(re.escape, self.parties)))

        name_only = mp
        # Special case surnames
        for surname in self.unique_case_surname:
            if name_only.startswith(surname):
                name_ordered = re.sub(r'^(\w+\b\s+\w+\b)\s+(.*)$', r'\1 \2', name_only)
                break
            else:
                name_ordered = re.sub(r'(.*?) (.*)', r'\1 \2', name_only)
        slug = slugify(name_ordered)

        # Check for a known correction
        slug = self.slug_corrections.get(slug, slug)

        # Handle unresolved slugs gracefully
        if slug is None:
            return None

        try:
            person = Person.objects.get(slug=slug)
            return person.slug
        except Person.DoesNotExist:
            print("Slug not found: {0}. Please find matching slug and add it to slug_corrections.".format(slug))
            return None



    def produce_json(self):
        data = self.groupings

        combined_data = self.combine_data(data)

        out = json.dumps(combined_data, indent=4, sort_keys=True)
        return re.sub(r' *$', '', out, flags=re.M)

    def combine_data(self, data):
        """
        Manipulate the data so that there are no duplicates of person and
        category, and sort data so that it is diff-able.
        """
        sorted_data = sorted(
            data,
            key=lambda x: x['person']['slug'] + ':' + x['category']['name']
        )

        combined_data = []

        for entry in sorted_data:
            # check if the last entry of combined_data has same person and
            # category. If so add entries to that, otherwise append whole thing.

            if len(combined_data):
                last_entry = combined_data[-1]
            else:
                last_entry = None

            if last_entry and last_entry['person']['slug'] == entry['person']['slug'] and last_entry['category']['name'] == entry['category']['name']:
                last_entry['entries'].extend(entry['entries'])
            else:
                combined_data.append(entry)

        return combined_data

    def extract_data_from_json(self):
        with open(self.filename) as fh:
            return json.load(fh)


if __name__ == "__main__":
    converter = Converter(sys.argv[1])
    output = converter.convert()
    print(output)

    if converter.finding_slug_corrections:
        print("\n\n")
        print("#### COPY THIS TO slug_corrections and s/null/None/ :) ####")
        print("\n\n")
        print(json.dumps(converter.slug_corrections, indent=4, sort_keys=True))
        print("\n\n")
