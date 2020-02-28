# -*- coding: utf-8 -*-

import os
from django.conf import settings
import requests

import socket
from contextlib import closing
from django.core.management import call_command
from io import BytesIO
from datetime import date
from mock import patch
from nose.plugins.attrib import attr
from instances.models import Instance

from instances.tests import InstanceTestCase
from popolo_name_resolver.resolve import EntityName, recreate_entities

from speeches.models import Speaker, Section
from pombola.za_hansard.importers.import_za_akomantoso import ImportZAAkomaNtoso, title_case_heading
from pombola.za_hansard.models import Source
from pombola_sayit.models import PombolaSayItJoin
from pombola.core.models import Person
from popolo.models import Person as PopoloPerson
from popolo_name_resolver.models import EntityName

import logging
logging.disable(logging.WARNING)
logger = logging.getLogger(__name__)


@attr(country='south_africa')
class ImportZAAkomaNtosoTests(InstanceTestCase):
    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 'test_inputs',
            'hansard')
        super(ImportZAAkomaNtosoTests, cls).setUpClass()
        call_command('update_index', interactive=False, verbosity=3)
        recreate_entities()

    def test_import_hansard_twice(self):
        Person.objects.all().delete()
        document_path = os.path.join(self._in_fixtures, 'SMALL_HANSARD.xml')

        speakers_before = Speaker.objects.count()

        # Import the same document twice
        an = ImportZAAkomaNtoso(instance=self.instance, commit=True)
        section1 = an.import_document(document_path)
        section2 = an.import_document(document_path)
        self.assertNotEqual(
            section1, section2,
            'The document should be imported as two different sections.')

        speaker_name = "Mr M S F Some Unknown Surname"
        speaker_count = Speaker.objects.filter(name=speaker_name).count()

        speakers_after = Speaker.objects.count()
        self.assertEqual(
            1, speaker_count,
            'Only one speaker should be created for %s, but %d were created' %
            (speaker_name, speaker_count))

    def test_import_hansard_speakers(self):
        # Delete test index
        requests.delete('http://elasticsearch:9200/pombola_test')

        document_name = 'NA200912.xml'
        document_path = os.path.join(self._in_fixtures, document_name)

        # Create Persons to identify
        PERSONS = [
            # Ms A C MASHISHI: debateBody -> debateSection -> debateSection -> speech
            Person.objects.create(title='Ms',
                                  legal_name='Agnes Christin Mashishi',
                                  family_name='Mashishi',
                                  given_name='Agnes Christin',
                                  slug='agnes-christin-mashishi'),
            # Dr P J RABIE
            Person.objects.create(title='Dr',
                                  legal_name='Petrus Johannes Rabie',
                                  family_name='Rabie',
                                  given_name='Petrus Johannes',
                                  slug='petrus-johannes-rabie'),
            # Ms L L VAN DER MERWE
            Person.objects.create(title='Ms',
                                  legal_name='Lilian Luca van der Merwe',
                                  family_name='van der Merwe',
                                  given_name='Lilian Luca',
                                  slug='lilian-luca-van-der-merwe'),
            # Mr M S F DE FREITAS
            Person.objects.create(title='Mr',
                                  legal_name='Mario Steven Foster De Freitas',
                                  family_name='de freita',
                                  given_name='Mario Steven Foster',
                                  slug='mario-steven-foster-de-freitas'),
        ]
        NUM_PERSONS = len(PERSONS)

        # Create Speakers for the persons
        call_command('pombola_sayit_sync_pombola_to_popolo', verbosity=3)
        self.assertEqual(NUM_PERSONS, PombolaSayItJoin.objects.count(),
                         'Speakers should be linked to persons.')
        for person in PERSONS:
            person.refresh_from_db()
            self.assertIsNotNone(
                person.sayit_link.sayit_speaker,
                'Speaker should be linked to person %s by pombola_sayit_sync_pombola_to_popolo'
                % (person.legal_name))

        SPEAKERS = [person.sayit_link.sayit_speaker for person in PERSONS]

        # Create EntityName objects
        call_command('popolo_name_resolver_init', verbosity=3)
        self.assertGreaterEqual(
            EntityName.objects.count(), NUM_PERSONS,
            'More than %d EntityNames should be created for speakers, but only %d were created.'
            % (NUM_PERSONS, EntityName.objects.count()))

        # Create Source
        source = Source.objects.create(
            title="Test hansard",
            document_name=document_name,
            document_number="001",
            url='api.pmg.org.za/test-hansard',
            language='English',
            last_processing_success=date.today(),
            house='NA',
            date=date.today(),
        )

        # Run the za_hansard_load_into_sayit command
        instance = Instance.objects.create(label='default')
        with patch.object(Source, 'xml_file_path', return_value=document_path):
            out = BytesIO()
            call_command('za_hansard_load_into_sayit', id=source.id, stdout=out)
            output = out.getvalue()
            self.assertIn('Imported 1 / 1 sections', output)
            lines = output.split('\n')
            # Get the section id of the section that was created
            for i in range(len(lines)-1, -1, -1):
                if lines[i].strip():
                    section_id = lines[i].strip("[]")
                    break

        section = Section.objects.get(id=int(section_id))

        self.assertTrue(section is not None,
                        'Hansard should be parsed into a non-null section.')

        # Get all the detected speakers from the speeches in the hansard
        detected_speakers = set()
        for section in section.children.all():
            for speech in section.speech_set.all():
                detected_speakers.add(speech.speaker)

        # print(detected_speakers)
        # self.assertFalse(True)
        # Check that the speakers were linked correctly to the above created Persons
        for speaker in SPEAKERS:
            self.assertIn(
                speaker, detected_speakers,
                '%s should be detected in the hansard as a speaker' %
                speaker.name)

    def test_title_casing(self):
        tests = (
            # initial, expected
            ("ALL CAPS", "All Caps"),
            ("MEMBER'S Statement", "Member's Statement"),
            ("member’s", "Member’s"),
        )

        for initial, expected in tests:
            self.assertEqual(title_case_heading(initial), expected)
