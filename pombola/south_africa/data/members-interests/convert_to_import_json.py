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
    finding_slug_corrections = False

    parties = ["ACDP", "AIC", "AL JAMA-AH", "ANC", "ATM", "COPE", "DA", "EFF", "FF PLUS", "GOOD", "IFP", "NFP", "PAC", "UDM"]
    unique_case_surname = ["ABRAHAM NTANTISO", "BODLANI MOTSHIDI", "LE GOFF", "MAZZONE MICHAEL", "MC GLUWA", "VAN ZYL", "NTLANGWINI LOUW", "DE BRUYN", "DENNER JORDAAN", "DU TOIT", "VAN STADEN"]

    slug_corrections = {
        "adrian-roos":"adrian-christopher-roos",
        "alexandra-amelia-abrahams":"alexandra-lilian-amelia-abrahams",
        "anna-tandi-moraka":"ms-moraka-anna-thandi",
        "barbara-dallas-creecy":"creecy-barbara",
        "bhekiziwe-abram-radebe":"bhekizizwe-abram-radebe",
        "cathlene-labuschagne":"cathleen-labuschagne",
        "christian-hans-hunsinger":"christian-hans-heinrich-hunsinger",
        "christian-hattingh":"chris-hattingh",
        "christopher-malematja":"cristopher-nakampe-malematja",
        "chupu-stanley-mathabatha":"mr-mathabatha-stanley-chupu",
        "david-douglas-des-van-rooyen":"david-douglas-van-rooyen",
        "david-masondo":"mr-masondo-david",
        "derleen-elana-james":"dereleen-elana-james",
        "desiree-van-der-walt":"d-van-der-walt",
        "diane-kohler":"dianne-kohler-barnard",
        "dorries-eunice-dlakude":"dorris-eunice-dlakude",
        "duduzile-zuma-sambudla":"duduzile-zumasambudla",
        "edward-mchunu":"es-mchunu",
        "eleanore-jacquelene-spies":"eleanore-rochelle-jacquelene-spies",
        "elsabe-natasha-ntlangwini-louw":"elsabe-natasha-louw",
        "enoch-godongwana":"e-godongwana",
        "haseenabanu-ismail":"haseena-ismail",
        "helen-elizabeth-neale-may":"helen-elizabeth-nealemay",
        "hendrik-christiaan-kruger":"hendrik-christiaan-crafford-kruger",
        "hlengiwe-octavia-mkhaliphi":"hlengiwe-octavia-hlophe",
        "igor-scheurkogel":"igor-stefan-scheurkogel",
        "jeanne-adriaanse":"venessa-adriaanse",
        "john-andile-mngxitam":"john-andile-mngxitama",
        "joseph-britz":"joseph-hendrik-pieter-britz",
        "judith-nemadzinga-tshabalala":"judith-tshabalala",
        "karabo-khakhau":"karabo-lerato-khakhau",
        "karl-willem-le-roux":"karl-willem-du-pre-le-roux",
        "kenneth-mosimanegare-mmoiemang":"mosimanegare-kenneth-mmoiemang",
        "kenneth-raselabe-meshoe":"kenneth-raselabe-joseph-meshoe",
        "kgomotso-anthea-ramolobeng":"anthea-ramolobeng",
        "khayelihle-madlala":"khayelihle-blessing-madlala",
        "khonziwe-hlonyana":"ntokozo-khonziwe-fortunate-hlonyana",
        "khumbudzo-silence-ntshavheni":"khumbudzo-phophi-silence-ntshavheni",
        "khusela-lwandlekazi-sangoni":"khusela-lwandlekazi-nobatembu-sangoni",
        "knowledge-malusi-gigaba":"knowledge-malusi-nkanyezi-gigaba",
        "kwenzokuhle-emerald-madlala":"emerald-kwenzokuhle-madlala",
        "lencel-masidika-komane":"lencel-mashidika-komane",
        "leonard-jones-leon-basson":"leonard-jones-basson",
        "luyolo-mphiti":"luyolo-mphithi",
        "lydia-sindisiwa-chikunga":"lydia-sindisiwe-chikunga",
        "mandla-matthewis-peter":"matthewis-mandla-peter",
        "mandlakayise-john-hlophe":"mandlakayise-john-hlope",
        "maropene-lydia-ramokgapa":"maropene-lydia-ramokgopa",
        "marshall-mzingisi-dlamini":"mzingisi-marshall-dlamini",
        "mathilda-bains":"mathilda-michelle-bains",
        "meisie-kennedy":"ms-kennedy-meisie",
        "mmapaseka-steve-letsike":"mmapaseka-steve-emily-letsike",
        "mmoba-solomon-malatsi":"mmoba-solomon-seshoka",
        "moleboheng-modise-mpya":"moleboheng-modise",
        "mondli-gungubele":"m-gungubele",
        "mpho-modise":"mpho-gift-modise",
        "mpho-parks-franklin-tau":"mpho-parks-franklyn-tau",
        "mzwanele-manyi":"mzwanele-jimmy-manyi",
        "namane-dickson-masemola":"mr-masemola-namane-dickson",
        "nanda-annah-ndalane":"ms-ndalane-nanda-anna",
        "natasha-wendy-anita-mazzone-michael":"natasha-wendy-anita-michael",
        "nhlanhla-mzungezwa-hadebe":"nhlanhla-hadebe",
        "nicholas-george-myburgh":"nicholas-georg-myburgh",
        "nicola-du-plessis":"nicola-susanna-du-plessis",
        "nolubabalo-mcinga":"nolubabalo-patience-mcinga",
        "nonceba-agnes-gcaleka-mazibuko":"nonceba-agnes-molwele",
        "nonkosi-queenie-mvana":"nonkosi-mvana",
        "nqabayomzi-lawrence-saziso-kwankwa":"nqabayomzi-lawrence-kwankwa",
        "ntombovuyo-veronica-mente":"ntombovuyo-veronica-nqweniso",
        "ofentse-jeremiah-mokae":"ofentse-mokae",
        "omphile-maotwe":"omphile-mankoba-confidence-maotwe",
        "paul-swart":"paul-john-swart",
        "pemmy-pamela-majodina":"pemmy-majodina",
        "phemelele-simelane-nkadimeng":"thembisile-nkadimeng",
        "phiroane-phala":"phiroene-phala",
        "poobalan-govender":"p-govender",
        "refilwe-mtshweni-tsipane":"refilwe-maria-mtshwenitsipane",
        "samantha-jane-graham-mare":"samantha-jane-graham",
        "samson-gwede-mantashe":"gwede-mantashe",
        "seaparo-charles-sekoati":"mr-sekoati-charles-seaparo",
        "sedukanelo-tshepo-louw":"sedukanelo-tshepo-david-louw",
        "seeng-mokoena":"julian-leseletsi-mokoena",
        "sheilla-tembalam-xego":"sheilla-tembalam-xego-sovita",
        "shipokosa-paulus-mashatile":"shipokosa-paul-mashatile",
        "sibongiseni-majola":"jerome-sibongiseni-majola",
        "sibongiseni-maxwell-dhlomo":"sm-dhlomo",
        "sifiso-zulu":"sifiso-advocate-zulu",
        "sihle-joel-ngubane":"joel-sihle-ngubane",
        "sinawo-thambo":"sinawo-tambo",
        "siyabonga-innocent-gama":"siyabonga-gama",
        "solly-mabebo":"baakisang-solomon-mabebo",
        "stanford-makashule-gana":"makashule-gana",
        "stella-tembisa-ndabeni":"stella-tembisa-ndabeni-abrahams",
        "supra-ramoeletsi-mahumapelo":"supra-mahumapelo",
        "sylivia-nxumalo":"cecilia-sylvia-nxumalo",
        "tebogo-kgosietsile-letlape":"tebogo-kgosietsile-solomon-letlape",
        "thalente-thuthukani-sakhile-kubheka":"thalente-thuthukani-sakhike-khubeka",
        "thandiswa-linnen-marawu":"thandiswa-marawu",
        "thembeka-buyisile-mchunu":"thembeka-vuyisile-buyisile-mchunu",
        "thembinkosi-siboniso-mjadu":"thembisile-siboniso-mjadu",
        "thokozile-elizabeth-magagula":"thokozile-magagula",
        "thomas-kaunda":"thomas-mxolisi-kaunda",
        "tshepo-lucky-montana":"lucky-montana",
        "tsholofelo-katlego-bodlani-motshidi":"tsholofelo-katlego-motshidi",
        "virgil-gericke":"virgill-gericke",
        "wendy-alexander":"wendy-robyn-alexander",
        "weziwe-tikana-gxotiwe":"weziwe-tikana",
        "willem-stephanus-aucamp":"willem-abraham-stephanus-aucamp",
        "windy-timotheus-plaatjies":"windy-timotheus-david-plaatjies",
        "zamathembu-ngcobo":"zamathembu-nokuthula-ngcobo",
        "shela-polly-boshielo":"shela-paulina-boshielo",
        "sisipho-palomina-jama":"sisipho-palomino-jama",
        "dorries-eunice-mpapane-dlakude":"dorris-eunice-dlakude",
        "nobuntu-lindumusa-hlazo-webster":"nobuntu-lindumusa-webster",
        "natasha-wendy-anita-mazzone":"natasha-wendy-anita-michael",
        "naledi-nokukhanya-chirwa-mpungose":"naledi-nokukhanya-chirwa",
        "ntombovuyo-veronica-mente-nkuna":"ntombovuyo-veronica-nqweniso",
        "nontando-judith-nolutshungu":"nontando-nolutshungu",
        "heloise-denner-jordaan":"heloise-denner",
        "hendrik-van-den-berg":"hendrik-jacobus-van-den-berg",
        "sibongiseni-sibongiseni-majola":"jerome-sibongiseni-majola",
        "pinky-pearlgene-mngadi":"pinky-pearlgene-ncube",
        "marlon-vivienne-daniels":"marlon-daniels",
        "general-bantubonke-harrington-holomisa":"bantubonke-harrington-holomisa",
        # Garbage entries
        "control-flag-ict": None
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
