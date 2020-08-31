from nose.plugins.attrib import attr
from django.test import TestCase

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
class OrganisationModelTest(TestCase):
    def setUp(self):
        create_organisation_kinds(self)
        create_organisations(self)
        create_contact_kinds(self)
        create_contacts(self)

    def create_identifiers(self):
        self.mysociety_id = Identifier.objects.create(
            identifier="/organisations/1",
            scheme="org.mysociety.za",
            object_id=self.test_organisation.id,
            content_type=ContentType.objects.get_for_model(Organisation),
        )

    def test_identifier(self):
        self.create_identifiers()
        org_mysociety_id = self.test_organisation.get_identifier("org.mysociety.za")
        self.assertEqual(org_mysociety_id, "/organisations/1")

    def test_email_addresses(self):
        self.assertEqual(0, len(self.test_organisation.email_addresses))
        na_contacts = self.na_organisation.email_addresses
        self.assertEqual(1, len(na_contacts))
        self.assertEqual([self.email_contact], na_contacts)
        self.assertTrue(self.na_organisation.has_email_address)
        self.assertFalse(self.test_organisation.has_email_address)

    def test_is_committee(self):
        self.assertTrue(self.na_organisation.is_committee)
        self.assertTrue(self.ncop_organisation.is_committee)
        self.assertFalse(self.test_organisation.is_committee)

    def test_contactable(self):
        self.assertTrue(self.na_organisation.contactable)
        self.assertFalse(self.ncop_organisation.contactable)
        self.assertFalse(self.test_organisation.contactable)

    def test_is_ongoing(self):
        self.assertTrue(self.na_organisation.is_ongoing())
        self.assertFalse(self.ncop_organisation.is_ongoing())
        self.assertTrue(self.test_organisation.is_ongoing())

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

    def test_has_email_contacts(self):
        result = Organisation.objects.has_email_contacts().all()
        self.assertIn(self.na_organisation, result)
        self.assertNotIn(self.test_organisation, result)
        self.assertNotIn(self.ncop_organisation, result)

    def test_contactable(self):
        result = Organisation.objects.has_email_contacts().all()
        self.assertIn(self.na_organisation, result)
        self.assertNotIn(self.test_organisation, result)
        self.assertNotIn(self.ncop_organisation, result)
