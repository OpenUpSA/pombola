from datetime import date, time

from django.test import TestCase
from django.core.management import call_command

from speeches.tests.helpers import create_sections
from speeches.models import Speech, Tag

from mock import patch
from pombola.za_hansard.models import Source


class OneOffTagSpeechesTests(TestCase):
    def setUp(self):

        subsections = [
            {
                "heading": "Nested section",
                "subsections": [
                    {
                        "heading": "Section with speeches",
                        "speeches": [4, date(2013, 3, 25), time(9, 0)],
                    },
                    {
                        "heading": "Bill on Silly Walks",
                        "speeches": [2, date(2013, 3, 25), time(12, 0)],
                    },
                ],
            },
            {
                "heading": "Another nested section (but completely empty)",
                "subsections": [],
            },
        ]

        create_sections(
            [
                {"heading": "Hansard", "subsections": subsections,},
                {"heading": "Committee Minutes", "subsections": subsections,},
                {
                    "heading": "Some Other Top Level Section",
                    "subsections": subsections,
                },
            ]
        )

    def test_tagging(self):
        # check that no speeches are tagged
        self.assertEqual(Speech.objects.filter(tags=None).count(), 18)

        call_command("za_hansard_one_off_tag_speeches")

        hansard = Tag.objects.get(name="hansard")
        committee = Tag.objects.get(name="committee")

        self.assertEqual(Speech.objects.filter(tags=None).count(), 6)
        self.assertEqual(Speech.objects.filter(tags=hansard).count(), 6)
        self.assertEqual(Speech.objects.filter(tags=committee).count(), 6)


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def raise_for_status(self):
            if self.status_code != 200:
                raise Exception()

    if args[0] == "https://api.pmg.org.za/hansard/":
        return MockResponse(
            {
                "count": 10,
                "next": False,
                "results": [{"url": "https://api.pmg.org.za/hansard/1-no-files/",},],
                "next": "https://api.pmg.org.za/hansard/?page=2",
            },
            200,
        )
    elif args[0] == "https://api.pmg.org.za/hansard/?page=2":
        return MockResponse(
            {
                "count": 10,
                "next": False,
                "results": [{"url": "https://api.pmg.org.za/hansard/2/",},],
            },
            200,
        )
    elif args[0] == "https://api.pmg.org.za/hansard/1-no-files/":
        return MockResponse(
            {
                "date": "2020-03-19T09:56:00+00:00",
                "title": "NCOP: Unrevised hansard",
                "url": "https://api.pmg.org.za/hansard/30075/",
            },
            200,
        )
    elif args[0] == "https://api.pmg.org.za/hansard/2/":
        return MockResponse(
            {
                "id": 1,
                "date": "2020-03-19T09:56:00+00:00",
                "title": "NA Unrevised hansard 2",
                "url": "https://api.pmg.org.za/hansard/2/",
                "house": {"name_short": "NA",},
                "type": "Test type",
                "files": [
                    {
                        "id": 1,
                        "title": "Test title",
                        "url": "https://api.pmg.org.za/hansard/2/files/1",
                    },
                    {"id": 2, "title": "File 2 is ignored",},
                ],
            },
            200,
        )

    return MockResponse(None, 404)


class ZaHansardCheckForNewSourcesFromPMGTests(TestCase):
    @patch(
        "pombola.za_hansard.management.commands.za_hansard_check_for_new_sources_from_pmg.requests.get",
        side_effect=mocked_requests_get,
    )
    def test_za_hansard_check_for_new_sources_from_pmg(self, requests_get_mock):
        count_before = Source.objects.count()

        call_command("za_hansard_check_for_new_sources_from_pmg", verbosity=2)

        count_after = Source.objects.count()
        created_sources = count_after - count_before

        self.assertEqual(1, created_sources)

        first_source = Source.objects.get(document_number=1)
        self.assertIsNotNone(first_source)
