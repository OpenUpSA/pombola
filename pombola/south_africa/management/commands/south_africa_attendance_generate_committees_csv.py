import csv
import json

import requests
from django.core.cache import caches
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from pombola.core.models import Organisation, OrganisationKind
from pombola.south_africa.management.commands.south_africa_attendance_fetch_pmg_committees import (
    committee_cache_slug, get_all_committees, get_pmg_api_cache)

OUT_FILE = "pa-pmg-committees"
CSV_FIELD_NAMES = ["id", "name", "pmg_name", "score"]
cache = get_pmg_api_cache()


def write_to_csv(data):
    file_path = OUT_FILE + ".csv"
    with open(file_path, "w") as f:
        print("Writing to %s" % file_path)
        writer = csv.DictWriter(f, fieldnames=CSV_FIELD_NAMES)

        writer.writeheader()
        for row in data:
            writer.writerow(row)


def write_to_json(data):
    file_path = OUT_FILE + ".json"
    with open(file_path, "w") as f:
        print("Writing to %s" % file_path)
        f.write(json.dumps(data, indent=4))


def get_pmg_result(c):
    result = cache.get(committee_cache_slug(c))
    if not result:
        raise Exception("No cached result for '%s'" % c.name)
    return result


def encode_to_utf8(data):
    return {
        k: v.encode("utf-8") if type(v) == unicode else v for k, v in data.iteritems()
    }


def committee_to_row(c):
    # Columns
    # id, name, pmg_name, search score, pmg_url

    # TODO: match pa_house, pmg_house (house_name)
    # TODO: match created_at dates

    data = {
        "id": c.id,
        "name": c.name,
    }
    pmg_result = get_pmg_result(c)
    if not pmg_result["results"]:
        data["score"] = 0
    else:
        sorted_results = sorted(pmg_result["results"], key=lambda x: -x["_score"])
        best_result = sorted_results[0]
        data["score"] = best_result["_score"]
        data["pmg_name"] = best_result["_source"]["title"]
    return encode_to_utf8(data)


class Command(BaseCommand):
    help = "Output CSV containing best committees matches"

    def handle(self, *args, **options):
        pa_committees = get_all_committees()
        data = sorted(
            [committee_to_row(c) for c in pa_committees], key=lambda x: x["score"]
        )
        # write_to_csv(data)
        write_to_json(data)
