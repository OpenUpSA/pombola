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

from django.contrib.contenttypes.models import ContentType


def create_organisation_kinds(self):
    self.foo_kind = OrganisationKind.objects.create(name="Foo", slug="foo",)
    self.na_kind = OrganisationKind.objects.create(
        name="National Assembly", slug="national-assembly-committees",
    )
    self.ncop_kind = OrganisationKind.objects.create(
        name="NCOP", slug="ncop-committees"
    )


def create_organisations(self):
    self.test_organisation = Organisation.objects.create(
        name="Test Org", slug="test-org", kind=self.foo_kind, ended="future"
    )

    self.na_organisation = Organisation.objects.create(
        name="Basic Education", slug="basic-education", kind=self.na_kind,
    )
    self.ncop_organisation = Organisation.objects.create(
        name="NCOP Appropriations",
        slug="ncop-appropriations",
        kind=self.ncop_kind,
        ended="2010-01-01",
    )


def create_contact_kinds(self):
    self.email_kind = ContactKind.objects.create(name="Email", slug="email")
    self.phone_kind = ContactKind.objects.create(name="Phone", slug="phone")


def create_contacts(self):
    self.email_contact = Contact.objects.create(
        kind=self.email_kind,
        value="test@example.com",
        content_type=ContentType.objects.get_for_model(self.na_organisation),
        object_id=self.na_organisation.id,
        preferred=True,
    )
    self.phone_contact = Contact.objects.create(
        kind=self.phone_kind,
        value="0000000",
        content_type=ContentType.objects.get_for_model(self.na_organisation),
        object_id=self.na_organisation.id,
        preferred=True,
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
class OrganisationOngoingUnitTest(unittest.TestCase):
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
class OrganisationModelTest(TestCase):
    def setUp(self):
        create_organisation_kinds(self)
        create_organisations(self)
        create_contact_kinds(self)
        create_contacts(self)

    def test_is_committee(self):
        self.assertTrue(self.na_organisation.is_committee)
        self.assertTrue(self.ncop_organisation.is_committee)
        self.assertFalse(self.test_organisation.is_committee)

    def test_contactable_committee(self):
        self.assertTrue(self.na_organisation.contactable_committee)
        self.assertFalse(self.ncop_organisation.contactable_committee)
        self.assertFalse(self.test_organisation.contactable_committee)

    def test_to_str(self):
        self.assertEqual(
            "Basic Education (National Assembly)", str(self.na_organisation)
        )


@attr(country="south_africa")
class OrganisationQuerySetTest(TestCase):
    def setUp(self):
        create_organisation_kinds(self)
        create_organisations(self)
        create_contact_kinds(self)
        create_contacts(self)

    def test_committees(self):
        result = Organisation.objects.committees().all()
        self.assertIn(self.na_organisation, result)
        self.assertIn(self.ncop_organisation, result)
        self.assertNotIn(self.test_organisation, result)

    def test_ongoing(self):
        result = Organisation.objects.ongoing().all()
        self.assertIn(self.na_organisation, result)
        self.assertIn(self.test_organisation, result)
        self.assertNotIn(self.ncop_organisation, result)

    def test_contactable(self):
        result = Organisation.objects.has_email_contacts().all()
        self.assertIn(self.na_organisation, result)
        self.assertNotIn(self.test_organisation, result)
        self.assertNotIn(self.ncop_organisation, result)
