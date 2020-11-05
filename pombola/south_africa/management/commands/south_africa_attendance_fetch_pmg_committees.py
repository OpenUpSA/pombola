import json

import requests
from django.core.management.base import BaseCommand, CommandError

BASE_URL = "https://api.pmg.org.za/committee/"

# while data['next']
PMG_COMMITTEES_FILE = "pmg-committees.json"


def write_to_json(data):
    with open(PMG_COMMITTEES_FILE, "w") as f:
        print("Writing to %s" % PMG_COMMITTEES_FILE)
        f.write(json.dumps(data, indent=4))


def add_response_to_data(data, response):
    results = response["results"]
    data.append(results)


def fetch_page(session, url):
    print("Fetching %s" % url)
    response = session.get(url)
    response.raise_for_status()
    return response.json()


class Command(BaseCommand):
    help = "Fetch all PMG committees and save in file"

    def handle(self, *args, **options):
        session = requests.Session()
        data = []
        response = fetch_page(session, BASE_URL)
        add_response_to_data(data, response)
        while response["next"]:
            try:
                response = fetch_page(session, response["next"])
                print("Next: %s" % response["next"])
            except Exception as e:
                print("Fetch failed with exception: %s" % e)
                break
            add_response_to_data(data, response)
        write_to_json(data)
