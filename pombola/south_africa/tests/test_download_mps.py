import datetime
import tempfile

from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django_date_extensions.fields import ApproximateDate
from nose.plugins.attrib import attr

import xlrd
from pombola.core.models import (
    Organisation,
    OrganisationKind,
    Person,
    Position,
    Contact,
    ContactKind,
)


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
            legal_name="Jimmy Stewart", slug="jimmy-stewart", email="jimmy@steward.com"
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
        email_kind = ContactKind.objects.create(slug="email")
        Contact.objects.create(
            content_type=ContentType.objects.get_for_model(self.mpl_a),
            object_id=self.mpl_a.id,
            kind=email_kind,
            value="jonathan@brink.com",
            preferred=True,
        )
        Position.objects.create(
            person=self.mpl_a,
            organisation=self.ncop,
            start_date=ApproximateDate(past=True),
            end_date=ApproximateDate(future=True),
        )
        self.mps = [self.mp_a]
        self.mpls = [self.mpl_a]
        self.all = self.mps + self.mpls
        # TODO: add inactive MP

    def test_download_all_mps(self):
        response = self.client.get(reverse("sa-download-members-xlsx"))
        xlsx_file = self.stream_xlsx_file(response)
        book = xlrd.open_workbook(filename=xlsx_file.name)
        self.assertEquals(1, book.nsheets)

        sheet = self.sheet = book.sheet_by_index(0)

        # Test headings
        self.check_headings()

        # Test values
        names = sheet.col_values(0)
        mobiles = sheet.col_values(1)
        emails = sheet.col_values(2)
        parties = sheet.col_values(3)

        for person in self.all:
            self.assertIn(person.name, names)
            if person.first_email:
                self.assertIn(person.first_email, emails)

    def stream_xlsx_file(self, response):
        f = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        for chunk in response.streaming_content:
            f.write(chunk)
        f.close()
        return f

    def check_headings(self):
        self.assertEqual(self.sheet.cell_value(0, 0), u"Name")
        self.assertEqual(self.sheet.cell_value(0, 1), u"Cell")
        self.assertEqual(self.sheet.cell_value(0, 2), u"Email")
        self.assertEqual(self.sheet.cell_value(0, 3), u"Parties")
