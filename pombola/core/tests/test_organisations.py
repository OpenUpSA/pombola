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


@attr(country="south_africa")
class OrganisationTest(TestCase):
    def create_contact_kinds(self):
        self.email_kind = ContactKind.objects.create(name="Email", slug="email")
        self.phone_kind = ContactKind.objects.create(name="Phone", slug="phone")

    def create_contacts(self):
        email_contact = Contact.objects.create(
            kind=self.email_kind,
            value="test@example.com",
            content_type=ContentType.objects.get_for_model(self.na_organisation),
            object_id=self.na_organisation.id,
            preferred=True,
        )

    def create_identifiers(self):
        self.mysociety_id = Identifier.objects.create(
            identifier="/organisations/1",
            scheme="org.mysociety.za",
            object_id=self.test_organisation.id,
            content_type=ContentType.objects.get_for_model(Organisation),
        )

    def setUp(self):
        self.foo_kind = OrganisationKind.objects.create(name="Foo", slug="foo",)
        self.na_kind = OrganisationKind.objects.create(
            name="National Assembly", slug="national-assembly-committees",
        )
        self.ncop_kind = OrganisationKind.objects.create(
            name="NCOP", slug="ncop-committees"
        )

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

        self.create_contact_kinds()
        self.create_contacts()

    def test_identifier(self):
        self.create_identifiers()
        org_mysociety_id = self.test_organisation.get_identifier("org.mysociety.za")
        self.assertEqual(org_mysociety_id, "/organisations/1")

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
