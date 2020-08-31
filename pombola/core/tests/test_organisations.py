from nose.plugins.attrib import attr
from django.test import TestCase

from pombola.core.models import Organisation, OrganisationKind, Identifier

from django.contrib.contenttypes.models import ContentType


@attr(country="south_africa")
class OrganisationModelTest(TestCase):
    def setUp(self):
        self.organisation_kind = OrganisationKind(name="Foo", slug="foo",)
        self.organisation_kind.save()

        self.organisation = Organisation(
            name="Test Org", slug="test-org", kind=self.organisation_kind,
        )
        self.organisation.save()

        self.mysociety_id = Identifier.objects.create(
            identifier="/organisations/1",
            scheme="org.mysociety.za",
            object_id=self.organisation.id,
            content_type=ContentType.objects.get_for_model(Organisation),
        )

    def testIdentifier(self):
        org_mysociety_id = self.organisation.get_identifier("org.mysociety.za")
        self.assertEqual(org_mysociety_id, "/organisations/1")

    def tearDown(self):
        self.mysociety_id.delete()
        self.organisation.delete()
        self.organisation_kind.delete()


@attr(country="south_africa")
class OrganisationQuerySetTest(TestCase):
    def setUp(self):
        self.foo_kind = OrganisationKind.objects.create(name="Foo", slug="foo",)
        self.na_kind = OrganisationKind.objects.create(
            name="National Assembly", slug="national-assembly-committees"
        )
        self.ncop_kind = OrganisationKind.objects.create(
            name="NCOP", slug="ncop-committees"
        )

        self.test_organisation = Organisation.objects.create(
            name="Test Org", slug="test-org", kind=self.foo_kind,
        )

        self.na_organisation = Organisation.objects.create(
            name="Basic Education", slug="basic-education", kind=self.na_kind,
        )
        self.ncop_organisation = Organisation.objects.create(
            name="NCOP Appropriations", slug="ncop-appropriations", kind=self.ncop_kind,
        )

    def testGetCommittees(self):
        result = Organisation.objects.committees().all()
        self.assertIn(self.na_organisation, result)
        self.assertIn(self.ncop_organisation, result)
        self.assertNotIn(self.test_organisation, result)