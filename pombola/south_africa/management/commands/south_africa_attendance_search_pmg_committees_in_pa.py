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
OUT_FILE = "pmg-pa-committees.json"


def write_to_json(data):
    file_path = OUT_FILE
    with open(file_path, "w") as f:
        print("Writing to %s" % file_path)
        f.write(json.dumps(data, indent=4))


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


class CustomResult(object):
    def __init__(self, score, object):
        self.score = score
        self.object = object


def search_pmg_committee_in_pa(c):
    name = c["name"]
    print("Searching for %s" % name)
    exact_match = Organisation.objects.filter(name__iexact=name).first()
    if exact_match:
        return [CustomResult(1, exact_match)]

    contains_match = Organisation.objects.filter(name__icontains=name).first()
    if contains_match:
        return [CustomResult(0.5, contains_match)]

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
        return query

    # Split query up into words and search for all of them

    terms = name.split()
    queries = [Q(name__icontains=term) for term in terms]
    django_query = reduce(operator.and_, queries)
    contains_match = Organisation.objects.filter(django_query).first()
    if contains_match:
        return [CustomResult(0.5, contains_match)]

    return []


def committee_to_row(pmg_committee, results):
    data = {
        "id_pmg": pmg_committee["id"],
        "name_pmg": pmg_committee["name"],
        "house_pmg": pmg_committee["house"]["name"],
        "num_meetings": pmg_committee["num_meetings"],
    }
    if len(results) > 0:
        best_result = results[0]
        data["score"] = best_result.score
        pa_organisation = best_result.object
        data["id_pa"] = pa_organisation.id
        data["name_pa"] = pa_organisation.name
        data["house_pa"] = pa_organisation.kind.name
    else:
        data["score"] = 0
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
                print("Best result: %s" % results[0].object)
                pass
            else:
                pass
            data.append(committee_to_row(pmg_committee, results))
        # sorted_data = sorted(data, key=lambda x: -x['score'])
        sorted_data = sorted(data, key=lambda x: -x["num_meetings"])
        write_to_json(sorted_data)

        zero_score = [d for d in data if d["score"] == 0]
        print("Number of committees: %d" % len(pmg_committees))
        print(
            "Number of zero-score committees: %d (%.2f%%)"
            % (len(zero_score), len(zero_score) * 100.0 / len(pmg_committees))
        )
