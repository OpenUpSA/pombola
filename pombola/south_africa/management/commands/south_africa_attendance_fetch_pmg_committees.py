import logging

import requests
from django.core.cache import caches
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from pombola.core.models import Organisation, OrganisationKind

logger = logging.getLogger(__name__)


COMMITTEE_ORGANISATION_KINDS = (
    11,
    12,
    13,
    14,
    15,
    19,
    20,
    22,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
)

cache = caches["pmg_api"]

PMG_SEARCH_URL = "https://api.pmg.org.za/search/?type=committee&q=%s"


def committee_cache_slug(committee):
    return "pmg-search-%s" % slugify(committee.name)


class Command(BaseCommand):
    help = "Fetch all committees from the PMG API and cache them in the pmg_api cache"

    def handle(self, *args, **options):
        pa_committees = Organisation.objects.filter(
            kind_id__in=COMMITTEE_ORGANISATION_KINDS
        )
        session = requests.Session()

        for pa_committee in pa_committees:
            cache_key = committee_cache_slug(pa_committee)
            if not cache.get(cache_key):

                # Search for committee PMG
                print("Searching for '%s' in PMG" % pa_committee.name)
                response = session.get(PMG_SEARCH_URL % pa_committee.name)

                # Cache results
                data = response.json()
                print(data)
                cache.set(cache_key, data)
            else:
                print("Found cached result for %s" % pa_committee.name)

            print("-" * 80)
