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

        email_kind = ContactKind.objects.get_or_create(slug="email")
        cell_kind = ContactKind.objects.get_or_create(slug="cell")

        self.mp_a = Person.objects.create(
            legal_name="Jimmy Stewart", slug="jimmy-stewart", email="jimmy@steward.com"
        )
        Position.objects.create(
            person=self.mp_a,
            organisation=self.na,
            start_date=ApproximateDate(past=True),
            end_date=ApproximateDate(future=True),
        )
        self.inactive_mp_a = Person.objects.create(
            legal_name="Stefan Terblanche", slug="stefan-terblanche"
        )
        Position.objects.create(
            person=self.mp_a,
            organisation=self.na,
            start_date=ApproximateDate(past=True),
            end_date=ApproximateDate(year=2009),
        )
        self.mpl_a = Person.objects.create(
            legal_name="Jonathan Brink", slug="jonathan-brink"
        )
        Contact.objects.create(
            content_type=ContentType.objects.get_for_model(self.mpl_a),
            object_id=self.mpl_a.id,
            kind=email_kind,
            value="jonathan@brink.com",
            preferred=True,
        )
        Contact.objects.create(
            content_type=ContentType.objects.get_for_model(self.mpl_a),
            object_id=self.mpl_a.id,
            kind=cell_kind,
            value="0123456789",
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
            if person.first_cell:
                self.assertIn(person.first_cell, mobiles)

        # Sheet should not contain inactive members
        self.assertNotIn(self.inactive_mp_a.name, names)

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
