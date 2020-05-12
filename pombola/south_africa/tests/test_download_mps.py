import datetime
import tempfile

from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TestCase
from nose.plugins.attrib import attr

import xlrd
from django_date_extensions.fields import ApproximateDate
from pombola.core.models import (Contact, ContactKind, Organisation,
                                 OrganisationKind, Person, Position)

COLUMN_INDICES = {"name": 0, "mobile": 1, "email": 2, "parties": 3}


@attr(country="south_africa")
class DownloadMPsTest(TestCase):
    def setUp(self):
        party = OrganisationKind.objects.create(name="Party", slug="party",)
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
        self.da = Organisation.objects.create(name="DA", kind=party, slug="da")
        self.anc = Organisation.objects.create(name="ANC", kind=party, slug="anc")

        email_kind = ContactKind.objects.create(slug="email", name="Email")
        cell_kind = ContactKind.objects.create(slug="cell", name="Cell")
        phone_kind = ContactKind.objects.create(slug="phone", name="Phone")

        self.mp_a = Person.objects.create(
            legal_name="Jimmy Stewart", slug="jimmy-stewart", email="jimmy@steward.com"
        )
        Position.objects.create(
            person=self.mp_a,
            organisation=self.na,
            start_date=ApproximateDate(past=True),
            end_date=ApproximateDate(future=True),
        )
        Position.objects.create(
            person=self.mp_a,
            organisation=self.da,
            start_date=ApproximateDate(past=True),
            end_date=ApproximateDate(future=True),
        )
        Contact.objects.create(
            content_type=ContentType.objects.get_for_model(self.mp_a),
            object_id=self.mp_a.id,
            kind=phone_kind,
            value="987654321",
            preferred=True,
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
        Position.objects.create(
            person=self.mp_a,
            organisation=self.da,
            start_date=ApproximateDate(past=True),
            end_date=ApproximateDate(year=2009),
        )
        Position.objects.create(
            person=self.mp_a,
            organisation=self.anc,
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

    def test_download_mps_index_page(self):
        response = self.client.get(reverse("sa-download-members-index"))
        self.assertIn("Download MPs in an Excel file", response.content)

    def test_download_all_mps(self):
        response = self.client.get(reverse("sa-download-members-xlsx"))
        xlsx_file = self.stream_xlsx_file(response)
        book = xlrd.open_workbook(filename=xlsx_file.name)
        self.assertEquals(1, book.nsheets)

        sheet = book.sheet_by_index(0)

        # Test headings
        self.check_headings(sheet)

        # Test values
        columns = self.get_columns(sheet)

        for person in self.all:
            self.assertIn(person.name, columns["names"])
            # Get the row
            row_num = columns["names"].index(person.name)
            row = sheet.row_values(row_num)
            if person.first_email:
                self.assertEqual(person.first_email, row[COLUMN_INDICES["email"]])
            if person.first_contact_number:
                self.assertEqual(
                    person.first_contact_number, row[COLUMN_INDICES["mobile"]]
                )
            self.assertEqual(",".join(person.parties()), row[COLUMN_INDICES["parties"]])

        # Sheet should not contain inactive members
        self.assertNotIn(self.inactive_mp_a.name, columns["names"])

    def test_download_mps(self):
        response = self.client.get(
            reverse("sa-download-members-xlsx") + "?house=national-assembly"
        )
        xlsx_file = self.stream_xlsx_file(response)
        book = xlrd.open_workbook(filename=xlsx_file.name)
        sheet = self.sheet = book.sheet_by_index(0)
        self.check_headings(sheet)
        columns = self.get_columns(sheet)
        for person in self.mps:
            self.assertIn(person.name, columns["names"])
        for person in self.mpls:
            self.assertNotIn(person.name, columns["names"])

    def test_download_mpls(self):
        response = self.client.get(reverse("sa-download-members-xlsx") + "?house=ncop")
        xlsx_file = self.stream_xlsx_file(response)
        book = xlrd.open_workbook(filename=xlsx_file.name)
        sheet = self.sheet = book.sheet_by_index(0)
        self.check_headings(sheet)
        columns = self.get_columns(sheet)
        for person in self.mpls:
            self.assertIn(person.name, columns["names"])
        for person in self.mps:
            self.assertNotIn(person.name, columns["names"])

    def stream_xlsx_file(self, response):
        f = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        for chunk in response.streaming_content:
            f.write(chunk)
        f.close()
        return f

    def check_headings(self, sheet):
        self.assertEqual(sheet.cell_value(0, COLUMN_INDICES["name"]), u"Name")
        self.assertEqual(sheet.cell_value(0, COLUMN_INDICES["mobile"]), u"Cell")
        self.assertEqual(sheet.cell_value(0, COLUMN_INDICES["email"]), u"Email")
        self.assertEqual(sheet.cell_value(0, COLUMN_INDICES["parties"]), u"Parties")

    def get_columns(self, sheet):
        return {
            "names": sheet.col_values(COLUMN_INDICES["name"]),
            "mobiles": sheet.col_values(COLUMN_INDICES["mobile"]),
            "emails": sheet.col_values(COLUMN_INDICES["email"]),
            "parties": sheet.col_values(COLUMN_INDICES["parties"]),
        }
