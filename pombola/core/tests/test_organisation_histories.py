from django.core.urlresolvers import reverse
from django.test import TestCase

from pombola.core import models


class OrganisationHistoryTest(TestCase):

    def setUp(self):
        organisation_kind = models.OrganisationKind.objects.create(
            name='Ad Hoc',
            slug='ad-hoc-committees',
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
            date_changed='2020-11-26'
            )

    def test_committes_page_has_history(self):
        """
        Tests that the committees page has history for the organisations.
        """
        response = self.client.get("/committees/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, " <p class='committee-history'>26 Nov 2020 | Formerly:<a href='/organisation/example-org1/'>\
                Example Organisation </a></p>",
            html=True
        )

    def test_organisation_page_has_history(self):
        """
        Tests that the organisation page has history for the organisations.
        """
        response = self.client.get("/organisation/example-org1/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, " <span class='committee-history'>26 Nov 2020 | Became:<a href='/organisation/example-org2/'>\
                Example Organisation2 </a></span>",
            html=True
        )
