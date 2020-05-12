import datetime
import tempfile

from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TestCase
from nose.plugins.attrib import attr

import xlrd
from django_date_extensions.fields import ApproximateDate
from pombola.core.models import (Contact, ContactKind, Organisation,
                                 OrganisationKind, Person, Position,
                                 PositionTitle)

COLUMN_INDICES = {"name": 0, "mobile": 1, "email": 2, "parties": 3}


def get_row_from_name(sheet, columns, name):
    row_num = columns["names"].index(name)
    return sheet.row_values(row_num)


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
        self.member = PositionTitle.objects.create(name="Member", slug="member")

        email_kind = ContactKind.objects.create(slug="email", name="Email")
        cell_kind = ContactKind.objects.create(slug="cell", name="Cell")
        phone_kind = ContactKind.objects.create(slug="phone", name="Phone")

        self.mp_a = Person.objects.create(
            legal_name="Jimmy Stewart", slug="jimmy-stewart", email="jimmy@steward.com"
        )
        # Create MP position at the National Assembly
        Position.objects.create(
            person=self.mp_a,
            organisation=self.na,
            start_date=ApproximateDate(past=True),
            end_date=ApproximateDate(future=True),
            title=self.member,
        )
        # MP currently active position at the DA
        Position.objects.create(
            person=self.mp_a,
            organisation=self.da,
            start_date=ApproximateDate(past=True),
            end_date=ApproximateDate(future=True),
            title=self.member,
        )
        # MP inactive position at the ANC
        Position.objects.create(
            person=self.mp_a,
            organisation=self.anc,
            start_date=ApproximateDate(past=True),
            end_date=ApproximateDate(year=2009),
        )
        # MP contact number
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
        # Create an inactive position at the NA for the inactive MP
        Position.objects.create(
            person=self.inactive_mp_a,
            organisation=self.na,
            start_date=ApproximateDate(past=True),
            end_date=ApproximateDate(year=2009),
        )
        # Create an MPL member
        self.mpl_a = Person.objects.create(
            legal_name="Jonathan Brink", slug="jonathan-brink"
        )
        # MPL email address
        Contact.objects.create(
            content_type=ContentType.objects.get_for_model(self.mpl_a),
            object_id=self.mpl_a.id,
            kind=email_kind,
            value="jonathan@brink.com",
            preferred=True,
        )
        # MPL contact number
        Contact.objects.create(
            content_type=ContentType.objects.get_for_model(self.mpl_a),
            object_id=self.mpl_a.id,
            kind=cell_kind,
            value="0123456789",
            preferred=True,
        )
        # MPL position at the NCOP
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

        # MP
        self.assertIn(self.mp_a.name, columns["names"])
        mp_a_row = get_row_from_name(sheet, columns, self.mp_a.name)
        self.assertEqual("jimmy@steward.com", mp_a_row[COLUMN_INDICES["email"]])
        self.assertEqual("987654321", mp_a_row[COLUMN_INDICES["mobile"]])
        self.assertEqual(self.da.name, mp_a_row[COLUMN_INDICES["parties"]])

        # MPL
        self.assertIn(self.mpl_a.name, columns["names"])
        mpl_a_row = get_row_from_name(sheet, columns, self.mpl_a.name)
        self.assertEqual("jonathan@brink.com", mpl_a_row[COLUMN_INDICES["email"]])
        self.assertEqual("0123456789", mpl_a_row[COLUMN_INDICES["mobile"]])
        self.assertEqual("", mpl_a_row[COLUMN_INDICES["parties"]])

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
