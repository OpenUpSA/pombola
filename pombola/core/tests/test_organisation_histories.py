from django.core.urlresolvers import reverse
from django.test import TestCase

from pombola.core import models


class OrganisationHistoryTest(TestCase):

    def setUp(self):
        organisation_kind = models.OrganisationKind.objects.create(
            name='New',
            slug='new',
            )
        org_old = models.Organisation.objects.create(
            slug='example-org1',
            name='Example Organisation',
            kind=organisation_kind,
            )
        org_new = models.Organisation.objects.create(
            slug='example-org2',
            name='Example Organisation2',
            kind=organisation_kind,
        )
        self.org_hist = models.OrganisationHistory.objects.create(
            old_organisation=org_old,
            new_organisation=org_new,
            date_changed='2020-09-12'
            )

    def test_new_history(self):

        self.assertEqual(self.org_hist.old_organisation.name, "Example Organisation")
        self.assertEqual(self.org_hist.new_organisation.name, "Example Organisation2")
