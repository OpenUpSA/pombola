from nose.plugins.attrib import attr
from django.test import TestCase
from django.utils import unittest

from pombola.core.models import (
    Organisation,
    OrganisationKind,
    Identifier,
    Contact,
    ContactKind,
)


@attr(country="south_africa")
class OrganisationEmailAddressesTest(TestCase):
    def setUp(self):
        self.test_kind = OrganisationKind.objects.create(
            name="TestKind", slug="test-kind"
        )
        self.organisation_without_emails = Organisation.objects.create(
            name="Test Org", slug="test-org", kind=self.test_kind
        )
        self.organisation_with_emails = Organisation.objects.create(
            name="Basic Education", slug="basic-education", kind=self.test_kind,
        )
        self.email_kind = ContactKind.objects.create(name="Email", slug="email")
        self.email_contact = Contact.objects.create(
            kind=self.email_kind,
            value="test@example.com",
            content_object=self.organisation_with_emails,
            preferred=True,
        )

    def test_email_addresses_property(self):
        self.assertEqual(0, len(self.organisation_without_emails.email_addresses))
        self.assertEqual(1, len(self.organisation_with_emails.email_addresses))
        self.assertEqual(
            [self.email_contact], self.organisation_with_emails.email_addresses
        )

    def test_has_email_address_property(self):
        self.assertTrue(self.organisation_with_emails.has_email_address)
        self.assertFalse(self.organisation_without_emails.has_email_address)

    def test_has_email_contacts_filter(self):
        result = Organisation.objects.has_email_contacts().all()
        self.assertIn(self.organisation_with_emails, result)
        self.assertNotIn(self.organisation_without_emails, result)


@attr(country="south_africa")
class OrganisationIsOngoingTest(unittest.TestCase):
    def setUp(self):
        self.test_kind = OrganisationKind(name="TestKind", slug="test-kind")
        self.organisation_future_ended = Organisation(
            name="Test Org", slug="test-org", kind=self.test_kind, ended="future"
        )
        self.organisation_none_ended = Organisation(
            name="Basic Education", slug="basic-education", kind=self.test_kind,
        )
        self.organisation_already_ended = Organisation(
            name="NCOP Appropriations",
            slug="ncop-appropriations",
            kind=self.test_kind,
            ended="2010-01-01",
        )

    def test_is_ongoing(self):
        self.assertTrue(self.organisation_future_ended.is_ongoing())
        self.assertTrue(self.organisation_none_ended.is_ongoing())
        self.assertFalse(self.organisation_already_ended.is_ongoing())


@attr(country="south_africa")
class OrganisationIdentifiersTest(TestCase):
    def setUp(self):
        self.test_kind = OrganisationKind.objects.create(
            name="TestKind", slug="test-kind"
        )
        self.test_organisation = Organisation.objects.create(
            name="Test Org", slug="test-org", kind=self.test_kind, ended="future"
        )
        self.mysociety_id = Identifier.objects.create(
            identifier="/organisations/1",
            scheme="org.mysociety.za",
            content_object=self.test_organisation,
        )

    def test_get_identifier(self):
        org_mysociety_id = self.test_organisation.get_identifier("org.mysociety.za")
        self.assertEqual(org_mysociety_id, "/organisations/1")


@attr(country="south_africa")
class OrganisationIsCommitteeTest(unittest.TestCase):
    def setUp(self):
        self.test_kind = OrganisationKind(name="TestKind", slug="test-kind")
        self.na_kind = OrganisationKind(
            name="National Assembly", slug="national-assembly-committees",
        )
        self.ncop_kind = OrganisationKind(name="NCOP", slug="ncop-committees")
        self.non_committee_org = Organisation(
            name="Non-committee",
            slug="non-committee",
            kind=self.test_kind,
            ended="future",
        )
        self.na_committee = Organisation(
            name="NA Committee", slug="na-committee", kind=self.na_kind, ended="future"
        )
        self.ncop_committee = Organisation(
            name="NCOP Committee",
            slug="ncop-committee",
            kind=self.ncop_kind,
            ended="future",
        )

    def test_is_committee(self):
        self.assertFalse(self.non_committee_org.is_committee)
        self.assertTrue(self.na_committee.is_committee)
        self.assertTrue(self.ncop_committee.is_committee)


@attr(country="south_africa")
class OrganisationToStrTest(TestCase):
    def setUp(self):
        self.test_kind = OrganisationKind(name="Test Kind", slug="test-kind")
        self.test_organisation = Organisation(
            name="Test Org", slug="test-org", kind=self.test_kind, ended="future"
        )

    def test_to_str(self):
        self.assertEqual("Test Org (Test Kind)", str(self.test_organisation))


@attr(country="south_africa")
class OrganisationContactableCommitteesTest(TestCase):
    def setUp(self):
        self.test_kind = OrganisationKind.objects.create(
            name="Test Kind", slug="test-kind"
        )
        self.email_kind = ContactKind.objects.create(name="Email", slug="email")

        self.na_kind = OrganisationKind.objects.create(
            name="National Assembly", slug="national-assembly-committees",
        )
        self.ncop_kind = OrganisationKind.objects.create(
            name="NCOP", slug="ncop-committees"
        )

        self.non_committee_org = Organisation.objects.create(
            name="Non-committee",
            slug="non-committee",
            kind=self.test_kind,
            ended="future",
        )
        self.ncop_committee_with_no_emails = Organisation.objects.create(
            name="NCOP Committee",
            slug="ncop-committee",
            kind=self.ncop_kind,
            ended="future",
        )
        self.na_committee_with_emails_future_ended = Organisation.objects.create(
            name="Basic Education",
            slug="basic-education",
            kind=self.na_kind,
            ended="future",
        )
        self.email_contact = Contact.objects.create(
            kind=self.email_kind,
            value="test@example.com",
            content_object=self.na_committee_with_emails_future_ended,
            preferred=True,
        )

    def test_contactable_filter(self):
        result = Organisation.objects.contactable_committees().all()
        self.assertIn(self.na_committee_with_emails_future_ended, result)
        self.assertNotIn(self.non_committee_org, result)
        self.assertNotIn(self.ncop_committee_with_no_emails, result)

    def test_contactable_committee_property(self):
        self.assertTrue(
            self.na_committee_with_emails_future_ended.contactable_committee
        )
        self.assertFalse(self.non_committee_org.contactable_committee)
        self.assertFalse(self.ncop_committee_with_no_emails.contactable_committee)


@attr(country="south_africa")
class OrganisationQuerysetCommitteesTest(TestCase):
    def setUp(self):
        self.test_kind = OrganisationKind.objects.create(
            name="Test Kind", slug="test-kind"
        )
        self.na_kind = OrganisationKind.objects.create(
            name="National Assembly", slug="national-assembly-committees",
        )
        self.ncop_kind = OrganisationKind.objects.create(
            name="NCOP", slug="ncop-committees"
        )

        self.non_committee_org = Organisation.objects.create(
            name="Non-committee",
            slug="non-committee",
            kind=self.test_kind,
            ended="future",
        )
        self.ncop_committee = Organisation.objects.create(
            name="NCOP Committee",
            slug="ncop-committee",
            kind=self.ncop_kind,
            ended="future",
        )
        self.na_committee = Organisation.objects.create(
            name="Basic Education",
            slug="basic-education",
            kind=self.na_kind,
            ended="future",
        )

    def test_committees_filter(self):
        result = Organisation.objects.committees().all()
        self.assertNotIn(self.non_committee_org, result)
        self.assertIn(self.ncop_committee, result)
        self.assertIn(self.na_committee, result)


@attr(country="south_africa")
class OrganisationQuerysetOngoingTest(unittest.TestCase):
    def setUp(self):
        self.test_kind = OrganisationKind.objects.create(
            name="TestKind", slug="test-kind"
        )
        self.organisation_future_ended = Organisation.objects.create(
            name="Test Org", slug="test-org", kind=self.test_kind, ended="future"
        )
        self.organisation_none_ended = Organisation.objects.create(
            name="Basic Education", slug="basic-education", kind=self.test_kind,
        )
        self.organisation_already_ended = Organisation.objects.create(
            name="NCOP Appropriations",
            slug="ncop-appropriations",
            kind=self.test_kind,
            ended="2010-01-01",
        )

    def test_ongoing_filter(self):
        result = Organisation.objects.ongoing().all()
        self.assertIn(self.organisation_future_ended, result)
        self.assertIn(self.organisation_none_ended, result)
        self.assertNotIn(self.organisation_already_ended, result)
