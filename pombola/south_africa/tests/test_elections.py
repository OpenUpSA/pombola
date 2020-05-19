from django.core.urlresolvers import reverse
from django.test import TestCase
from nose.plugins.attrib import attr

from django_date_extensions.fields import ApproximateDate, ApproximateDateField
from info.models import InfoPage
from mock import Mock
from pombola.core.models import (Organisation, OrganisationKind, Person, Place,
                                 PlaceKind, Position, PositionTitle)
from pombola.south_africa.views.elections import get_candidate_ranking_sort_key


@attr(country="south_africa")
class ProvincialElectionViewTest(TestCase):
    def setUp(self):
        self.province_name = "north-west"
        provincial_list_slug = "-provincial-%s-election-list-2019" % self.province_name

        self.province_kind = PlaceKind.objects.create(name="Province", slug="province",)
        self.province = Place.objects.create(
            kind=self.province_kind, slug=self.province_name, name=self.province_name
        )
        self.party_kind = OrganisationKind.objects.create(name="Party", slug="party",)
        self.election_list_kind = OrganisationKind.objects.create(
            name="Election List", slug="election-list",
        )
        self.party_da = Organisation.objects.create(
            slug="da", name="DA", kind=self.party_kind
        )

        self.election_list_da = Organisation.objects.create(
            slug=(self.party_da.slug + provincial_list_slug),
            name="DA Election List",
            kind=self.election_list_kind,
        )

        self.candidate_a = Person.objects.create(
            legal_name="Tom Jones", slug="tom-jones"
        )

        position = Position.objects.create(
            person=self.candidate_a,
            organisation=self.election_list_da,
            start_date=ApproximateDate(2016),
            end_date=ApproximateDate(2020),
            title=PositionTitle.objects.create(
                name="1st Candidate", slug="1st-candidate"
            ),
        )

    def test_sa_election_province_candidates_view(self):
        url = reverse(
            "sa-election-candidates-provincial", args=[2019, self.province_name]
        )
        response = self.client.get(url)
        self.assertIn(self.candidate_a.name, response.content)

    def test_sa_election_province_party_candidates_view(self):
        url = reverse(
            "sa-election-candidates-provincial-party",
            args=[2019, self.province_name, "da"],
        )
        response = self.client.get(url)
        self.assertIn(self.candidate_a.name, response.content)


@attr(country="south_africa")
class TestGetCandidateRankingSortKey(TestCase):
    def test_get_ranking_from_number(self):
        candidate_a = Mock()
        candidate_a.title.name = "1st Candidate"
        candidate_b = Mock()
        candidate_b.title.name = "2st Candidate"
        self.assertEqual(1, get_candidate_ranking_sort_key(candidate_a))
        self.assertEqual(2, get_candidate_ranking_sort_key(candidate_b))

    def test_get_ranking_when_no_number_present(self):
        candidate_a = Mock()
        candidate_a.title.name = "Member"
        candidate_b = Mock()
        candidate_b.title.name = ""
        self.assertEqual("", get_candidate_ranking_sort_key(candidate_a))
        self.assertEqual("", get_candidate_ranking_sort_key(candidate_b))
