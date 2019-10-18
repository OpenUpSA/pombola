# Tests for the Django management commands (i.e. those invoked with
# ./manage.py or django-admin.py).

import contextlib
from mock import patch
import sys

from pombola.core.models import (
    Contact,
    ContactKind,
    Organisation,
    OrganisationKind,
    OrganisationRelationship,
    OrganisationRelationshipKind,
    ParliamentarySession,
    Person,
    Place,
    PlaceKind,
    Position,
    PositionTitle,
)

from pombola.za_hansard.management.commands.za_hansard_q_and_a_scraper import Command
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


# A context manager to suppress standard output, as suggested in:
# http://stackoverflow.com/a/1810086/223092

@contextlib.contextmanager
def no_stdout_or_stderr():
    save_stdout = sys.stdout
    save_stderr = sys.stderr

    class DevNull(object):
        def write(self, _): pass
    sys.stdout = DevNull()
    sys.stderr = DevNull()
    try:
        yield
    finally:
        sys.stdout = save_stdout
        sys.stderr = save_stderr


class MergeObjectsCommandTest(TestCase):
    def setUp(self):
        self.person_a = Person.objects.create(
            name="Jimmy Stewart",
            slug="jimmy-stewart")
        self.person_b = Person.objects.create(
            name="James Stewart",
            slug="james-stewart")

        self.organisation_kind = OrganisationKind.objects.create(
            name="Example Organisations",
            slug="example-orgs")

        self.organisation_a = Organisation.objects.create(
            name="Organisation A",
            kind=self.organisation_kind,
            slug="organisation-a")
        self.organisation_b = Organisation.objects.create(
            name="Organisation B",
            kind=self.organisation_kind,
            slug="organisation-b")
        self.organisation_c = Organisation.objects.create(
            name="Organisation C",
            kind=self.organisation_kind,
            slug="organisation-c")

        self.position_title = PositionTitle.objects.create(
            name="Member")

        self.position_a = Position.objects.create(
            title=self.position_title,
            person=self.person_a,
            category="other",
            organisation=self.organisation_a)
        self.position_b = Position.objects.create(
            title=self.position_title,
            person=self.person_b,
            category="other",
            organisation=self.organisation_b)

        self.org_relationship_kind = OrganisationRelationshipKind.objects.create(
            name="Test Org Kind")

        self.org_relationship_b_c = OrganisationRelationship.objects.create(
            kind=self.org_relationship_kind,
            organisation_a=self.organisation_b,
            organisation_b=self.organisation_c,
            )
        self.org_relationship_b_a = OrganisationRelationship.objects.create(
            kind=self.org_relationship_kind,
            organisation_a=self.organisation_c,
            organisation_b=self.organisation_b,
            )

        self.place_kind = PlaceKind.objects.create(
            name='Test PlaceKind',
            slug='test-placekind',
            )

        self.place = Place.objects.create(
            name='Test Place',
            slug='test-place',
            kind=self.place_kind,
            organisation=self.organisation_b,
            )

        self.parliamentary_session = ParliamentarySession.objects.create(
            name='Test Parliamentary Session',
            slug='test-parliamentary-session',
            house=self.organisation_b,
            )

        self.phone_kind = ContactKind.objects.create(
            slug="example-phones",
            name="Phone Number")
        self.email_kind = ContactKind.objects.create(
            slug="example-emails",
            name="Email Address")

        self.contact_a = Contact.objects.create(
            content_type = ContentType.objects.get_for_model(Person),
            object_id = self.person_a.id,
            kind = self.phone_kind,
            value = '555 5555',
            preferred=False,
        )
        self.contact_a.save()
        self.contact_b = Contact.objects.create(
            content_type=ContentType.objects.get_for_model(Person),
            object_id=self.person_b.id,
            kind=self.email_kind,
            value='jimmy@example.org',
            preferred=False,
        )
        self.contact_b.save()

        self.options = {
            'keep_object': self.person_a.id,
            'delete_object': self.person_b.id,
            'sayit_id_scheme': 'org.mysociety.pombolatest',
            'quiet': True,
            'interactive': False,
        }

        self.org_options = {
            'keep_object': self.organisation_a.id,
            'delete_object': self.organisation_b.id,
            'quiet': True,
            'interactive': False,
        }

    def test_merge_people_conflicting_dob(self):
        self.person_a.date_of_birth = "1908-05-20"
        self.person_a.save()

        self.person_b.date_of_birth = "1908-05-21"
        self.person_b.save()

        # There should be an error - this would lose the B version of
        # the date of birth:
        with self.assertRaises(CommandError):
            with no_stdout_or_stderr():
                call_command('core_merge_people', **self.options)

    def test_merge_people_losing_summary(self):
        self.person_a.summary = ""
        self.person_a.date_of_birth = "1908-05-20"
        self.person_a.save()

        self.person_b.summary = "The famous actor."
        self.person_b.date_of_birth = "1908-05-20"
        self.person_b.save()

        # This should also error - it would lose the B version of the
        # summary field:
        with self.assertRaises(CommandError):
            with no_stdout_or_stderr():
                call_command('core_merge_people', **self.options)

    def test_merge_people(self):
        # This one should succeed:
        with no_stdout_or_stderr():
            call_command('core_merge_people', **self.options)

        # Check that only person_a exists any more:
        Person.objects.get(pk=self.person_a.id)
        with self.assertRaises(Person.DoesNotExist):
            Person.objects.get(pk=self.person_b.id)

        # Check that both positions are present on the kept person:
        self.assertEqual(1, Position.objects.filter(
                person=self.person_a,
                title=self.position_title,
                organisation=self.organisation_a).count())
        self.assertEqual(1, Position.objects.filter(
                person=self.person_a,
                title=self.position_title,
                organisation=self.organisation_b).count())

        # Check that there are now two contacts for the kept person:
        contacts = Contact.objects.filter(
            content_type=ContentType.objects.get_for_model(Person),
            object_id=self.person_a.id).order_by('value')
        self.assertEqual(2, contacts.count())
        self.assertEqual(contacts[0].value, '555 5555')
        self.assertEqual(contacts[1].value, 'jimmy@example.org')

    def test_merge_people_with_slugs(self):
        options = {
            'keep_object': self.person_a.slug,
            'delete_object': self.person_b.slug,
            'sayit_id_scheme': 'org.mysociety.pombolatest',
            'quiet': True,
            'interactive': False
        }
        with no_stdout_or_stderr():
            call_command('core_merge_people', **options)

        # Check that only person_a exists any more:
        Person.objects.get(pk=self.person_a.id)
        with self.assertRaises(Person.DoesNotExist):
            Person.objects.get(pk=self.person_b.id)

    @patch('__builtin__.raw_input', return_value='n')
    def test_merge_people_no_continue(self, mock_input):
        options = {
            'keep_object': self.person_a.id,
            'delete_object': self.person_b.id,
            'sayit_id_scheme': 'org.mysociety.pombolatest',
            'quiet': True
        }
        with self.assertRaises(CommandError):
            with no_stdout_or_stderr():
                call_command('core_merge_people', **options)

        # Check that nothing was deleted:
        Person.objects.get(pk=self.person_a.id)
        Person.objects.get(pk=self.person_b.id)

    def test_merge_people_inputs_are_the_same(self):
        options = {
            'keep_object': self.person_a.id,
            'delete_object': self.person_a.slug,
            'sayit_id_scheme': 'org.mysociety.pombolatest',
            'quiet': True
        }

        with self.assertRaises(CommandError):
            with no_stdout_or_stderr():
                call_command('core_merge_people', **options)

    def test_merge_people_differing_hidden_states(self):
        self.person_a.hidden = False
        self.person_a.save()

        self.person_b.hidden = True
        self.person_b.save()

        with self.assertRaises(CommandError):
            with no_stdout_or_stderr():
                call_command('core_merge_people', **self.options)

    def test_merge_orgs(self):
        # This one should succeed:
        with no_stdout_or_stderr():
            call_command('core_merge_organisations', **self.org_options)

        # Check that only organisation_a exists any more:
        Organisation.objects.get(pk=self.organisation_a.id)
        with self.assertRaises(Organisation.DoesNotExist):
            Organisation.objects.get(pk=self.organisation_b.id)

        # Check that both positions are present on the kept organisation:
        self.assertEqual(1, Position.objects.filter(
                person=self.person_a,
                title=self.position_title,
                organisation=self.organisation_a).count())
        self.assertEqual(1, Position.objects.filter(
                person=self.person_b,
                title=self.position_title,
                organisation=self.organisation_a).count())

        # Check that organisation relationships from both directions are
        # updated.
        self.assertEqual(1, OrganisationRelationship.objects.filter(
                kind=self.org_relationship_kind,
                organisation_a=self.organisation_a,
                organisation_b=self.organisation_c).count())
        self.assertEqual(1, OrganisationRelationship.objects.filter(
                kind=self.org_relationship_kind,
                organisation_a=self.organisation_c,
                organisation_b=self.organisation_a).count())

        # Check that places get the correct org
        self.assertEqual(1, Place.objects.filter(
                kind=self.place_kind,
                slug='test-place',
                organisation=self.organisation_a).count())

        # Check that ParliamentarySession objects get the correct org.
        self.assertEqual(1, ParliamentarySession.objects.filter(
                slug='test-parliamentary-session',
                house=self.organisation_a).count())

    def test_merge_orgs_conflicting_started(self):
        self.organisation_a.started = "1908-05-20"
        self.organisation_a.save()

        self.organisation_b.started = "1908-05-21"
        self.organisation_b.save()

        # There should be an error - this would lose the B version of
        # the date of birth:
        with self.assertRaises(CommandError):
            with no_stdout_or_stderr():
                call_command('core_merge_organisations', **self.org_options)

    def test_merge_orgs_losing_summary(self):
        self.organisation_a.summary = ""
        self.organisation_a.started = "1908-05-20"
        self.organisation_a.save()

        self.organisation_b.summary = "The famous actor."
        self.organisation_b.started = "1908-05-20"
        self.organisation_b.save()

        # This should also error - it would lose the B version of the
        # summary field:
        with self.assertRaises(CommandError):
            with no_stdout_or_stderr():
                call_command('core_merge_organisations', **self.org_options)

    def test_merge_orgs_with_slugs(self):
        options = {
            'keep_object': self.organisation_a.slug,
            'delete_object': self.organisation_b.slug,
            'quiet': True,
            'interactive': False
        }
        with no_stdout_or_stderr():
            call_command('core_merge_organisations', **options)

        # Check that only organisation_a exists any more:
        Organisation.objects.get(pk=self.organisation_a.id)
        with self.assertRaises(Organisation.DoesNotExist):
            Organisation.objects.get(pk=self.organisation_b.id)


class ZAHansardQAndAScraperTest(TestCase):
    def setUp(self):
        self.question = {u'code': u'NW1264', u'written_number': 1264, u'house': {
            u'contact_details': None, u'name': u'National Assembly',
            u'name_short': u'NA', u'sphere': u'national', u'id': 3,
            u'speaker_id': None},
            u'updated_at': u'2018-06-19T13:58:42.212441+02:00',
            u'source_file': {u'description': None, u'origname': None,
                             u'title': None, u'file_mime': u'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                             u'file_path': u'RNW1264-180605.docx', u'file_bytes': 18537,
                             u'url': u'https://pmg.org.za/files/RNW1264-180605.docx',
                             u'playtime': None, u'id': 115341}, u'year': 2018,
            u'president_number': None, u'asked_by_member': {
                u'questions_url': u'https://api.pmg.org.za/member/242/questions/',
                u'bio': u'',
                u'pa_link': u'https://www.pa.org.za/person/semakaleng-patricia-kopane/',
                u'house_id': 3, u'name': u'Kopane, Ms SP',
                u'url': u'https://api.pmg.org.za/member/242/',
                u'attendance_url': u'https://api.pmg.org.za/member/242/attendance/',
                u'created_at': u'2015-10-08T15:28:40.761504+02:00',
                u'updated_at': u'2019-07-31T12:55:19.771434+02:00',
                u'start_date': u'2013-04-09', u'current': True,
                u'profile_pic_url': u'http://pmg-assets.s3-website-eu-west-1.amazonaws.com/Kopane_SP.jpg', u'party_id': 2, u'pa_url': u'https://www.pa.org.za/person/semakaleng-patricia-kopane/', u'party': {u'id': 2, u'name': u'DA'}, u'province_id': None, u'id': 242
        }, u'id': 9117,
            u'question': u'(1) (a) What is the annual budget of the SA National Aids Council (SANAC)?',
                         u'asked_by_member_id': 242, u'source_file_id': 115341,
                         u'answer_type': u'oral',
                         u'answer': u'<p>The Annual budget of SANAC for the period 2017/18 was R66, 275,268</p>',
                         u'intro': u'Ms S P Kopane (DA) to ask the Deputy President:', u'question_to_name': u'Deputy President', u'question_number': 1264, u'date': u'2018-06-05', u'asked_by_name': u'Ms S P Kopane', u'house_id': 3, u'url': u'https://api.pmg.org.za/committee-question/9117/', u'created_at': u'2018-06-19T13:57:12.892916+02:00', u'deputy_president_number': None, u'translated': False, u'oral_number': None, u'minister_id': 37}

    def test_oral_question(self):
        command = Command()
        try:
            command.handle_api_question_and_reply(self.question)
        except Exception:
            self.fail("No exception should be thrown for oral question type.")
