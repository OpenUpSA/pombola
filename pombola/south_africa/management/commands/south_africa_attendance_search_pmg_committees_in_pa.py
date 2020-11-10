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

PMG_COMMITTEES_FILE = "pmg-committees.json"
JSON_OUT_FILE = "pmg-pa-committees.json"
CSV_OUT_FILE = "pmg-pa-committees.csv"


def write_to_json(data):
    file_path = JSON_OUT_FILE
    with open(file_path, "w") as f:
        print("Writing to %s" % file_path)
        f.write(json.dumps(data, indent=4))


def encode_to_utf8(data):
    return {
        k: v.encode("utf-8") if type(v) == unicode else v for k, v in data.iteritems()
    }


def csv_row(d):
    data = {
        "id_pmg": d["id_pmg"],
        "name_pmg": d["name_pmg"],
        "house_pmg": d["house_pmg"],
        "num_meetings": d["num_meetings"],
    }
    for i, result in enumerate(d["results"][:4]):
        data["pa_name_%d" % i] = result["name_pa"]
        data["pa_house_%d" % i] = result["house_pa"]
        data["pa_link_%d" % i] = result["admin_link_pa"]
    return encode_to_utf8(data)


def write_to_csv(data):
    file_path = CSV_OUT_FILE
    headings = ["id_pmg", "num_meetings", "name_pmg", "house_pmg"]
    for i in range(4):
        headings += ["pa_name_%d" % i, "pa_house_%d" % i, "pa_link_%d" % i]

    with open(file_path, "w") as f:
        print("Writing to %s" % file_path)
        writer = csv.DictWriter(f, fieldnames=headings)
        writer.writeheader()
        for d in data:
            writer.writerow(csv_row(d))


def read_pmg_committees():
    with open(PMG_COMMITTEES_FILE, "r") as f:
        return json.loads(f.read())


def generate_fuzzy_query_object(query_string):
    if re.match("^[a-z0-9 ]*$", query_string, re.IGNORECASE):
        query_string = " ".join(word + "~1" for word in query_string.split(" "))
        query_object = Raw(query_string)
    else:
        query_object = AutoQuery(query_string)
    return query_object


def search_pmg_committee_in_pa(c):
    name = c["name"]
    print("Searching for %s" % name)

    # See if there's an exact match
    exact_matches = Organisation.objects.filter(name__iexact=name)
    if exact_matches.exists():
        return exact_matches

    # See if there's a committee that contains this name
    contains_matches = Organisation.objects.filter(name__icontains=name)
    if contains_matches.exists():
        return contains_matches

    # Split query up into words and see if there's a committee that contains all of them
    terms = [term.lower() for term in name.split()]
    queries = [Q(name__icontains=term) for term in terms]
    django_query = reduce(operator.and_, queries)
    contains_matches = Organisation.objects.filter(django_query)
    if contains_matches.exists():
        return contains_matches

    # Search in ElasticSearch
    query = SearchQuerySet().models(*[Organisation])
    defaults = {
        "model": Organisation,
        "title": "Organisations",
    }
    extra_filter = defaults.get("filter", {})
    filter_args = extra_filter.get("args", [])
    filter_kwargs = extra_filter.get("kwargs", {})
    query = query.filter(
        content=generate_fuzzy_query_object(name), *filter_args, **filter_kwargs
    )
    if len(query):
        return [result.object for result in query]

    # Remove common words and search again
    terms = set(terms)
    common_words = {
        "of",
        "the",
        "and",
        "committee",
        "ad",
        "hoc",
        "joint",
        "inactive",
        "(inactive)",
        "to",
        "public",
        "&",
        "ncop",
    }
    terms -= common_words
    queries = [Q(name__icontains=term) for term in terms]
    django_query = reduce(operator.and_, queries)
    contains_matches = Organisation.objects.filter(django_query)
    if contains_matches.exists():
        return contains_matches

    return []


def committee_to_row(pmg_committee, results):
    data = {
        "id_pmg": pmg_committee["id"],
        "name_pmg": pmg_committee["name"],
        "house_pmg": pmg_committee["house"]["name"],
        "num_meetings": pmg_committee["num_meetings"],
        "results": [],
    }
    for pa_organisation in results:
        data["results"].append(
            {
                "id_pa": pa_organisation.id,
                "name_pa": pa_organisation.name,
                "house_pa": pa_organisation.kind.name,
                "link_pa": "https://www.pa.org.za/organisation/%s/"
                % pa_organisation.slug,
                "admin_link_pa": "https://www.pa.org.za/admin/core/organisation/%d/"
                % pa_organisation.id,
            }
        )

    return data


class Command(BaseCommand):
    help = "For each PMG committee, search for it in PA and save the results"

    def handle(self, *args, **options):
        pmg_committees = read_pmg_committees()
        data = []
        for pmg_committee in pmg_committees:
            results = search_pmg_committee_in_pa(pmg_committee)
            results_count = len(results)
            print("Found %d results" % results_count)
            if results_count > 0:
                print("Best result: %s" % results[0])
            else:
                print("No result found")
            data.append(committee_to_row(pmg_committee, results))

        sorted_data = sorted(data, key=lambda x: -x["num_meetings"])
        write_to_json(sorted_data)
        write_to_csv(sorted_data)

        print("Number of committees: %d" % len(pmg_committees))
