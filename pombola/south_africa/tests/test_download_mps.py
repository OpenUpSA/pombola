import datetime
import tempfile

from django.core.urlresolvers import reverse
from django.test import TestCase
from django_date_extensions.fields import ApproximateDate
from nose.plugins.attrib import attr

import xlrd
from pombola.core.models import (Organisation, OrganisationKind, Person,
                                 Position)


@attr(country="south_africa")
class DownloadMPsTest(TestCase):
    def setUp(self):
        parliament = OrganisationKind.objects.create(
            name="Parliament", slug="parliament",
        )
        provincial_legislature = OrganisationKind.objects.create(
            name="Provincial Legislature", slug="provincial-legislature",
        )

        self.na = Organisation.objects.create(
            name="National Assembly", kind=parliament, slug="national-assembly",
        )
        self.ncop = Organisation.objects.create(
            name="NCOP", kind=provincial_legislature, slug="ncop",
        )
        self.mp_a = Person.objects.create(
            legal_name="Jimmy Stewart", slug="jimmy-stewart"
        )
        Position.objects.create(
            person=self.mp_a,
            organisation=self.na,
            start_date=ApproximateDate(past=True),
            end_date=ApproximateDate(future=True),
        )
        self.mpl_a = Person.objects.create(
            legal_name="Jonathan Brink", slug="jonathan-brink"
        )
        Position.objects.create(
            person=self.mpl_a,
            organisation=self.ncop,
            start_date=ApproximateDate(past=True),
            end_date=ApproximateDate(future=True),
        )
        self.mps = [self.mp_a]
        self.mpls = [self.mpl_a]

    def test_download_all_mps(self):
        response = self.client.get(reverse("sa-download-members-xlsx"))
        f = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        for chunk in response.streaming_content:
            f.write(chunk)
        f.close()
        book = xlrd.open_workbook(filename=f.name)
        self.assertEquals(1, book.nsheets)
        sheet = book.sheet_by_index(0)
        names = [cell.value for cell in sheet.col(0)]
        self.assertEqual(names[0], u"Name")
        for mp in self.mps:
            self.assertIn(mp.name, names)
