# -*- coding: utf-8 -*-

import os

from django.core.management import call_command

from instances.tests import InstanceTestCase
from popolo_name_resolver.resolve import EntityName, recreate_entities

from speeches.models import Speaker
from pombola.za_hansard.importers.import_za_akomantoso import ImportZAAkomaNtoso, title_case_heading
from pombola_sayit.models import PombolaSayItJoin
from pombola.core.models import Person
from popolo.models import Person as PopoloPerson
from popolo_name_resolver.models import EntityName

import logging
# logging.disable(logging.WARNING)
logger = logging.getLogger(__name__)


class ImportZAAkomaNtosoTests(InstanceTestCase):
    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 'test_inputs',
            'hansard')
        super(ImportZAAkomaNtosoTests, cls).setUpClass()
        call_command('update_index', interactive=False, verbosity=3)
        recreate_entities()

    def test_import_import_hansard_speakers(self):
        logger.debug("logging.debug: XXXXXX I need to see logs")
        document_path = os.path.join(self._in_fixtures, 'NA200912.xml')

        # Create Persons to identify
        PERSONS = [
            # Ms A C MASHISHI: debateBody -> debateSection -> debateSection -> speech
            Person.objects.create(title='Ms',
                                  legal_name='Agnes Christin Mashishi',
                                  slug='agnes-christin-mashishi'),
            # Dr P J RABIE
            Person.objects.create(title='Dr',
                                  legal_name='Petrus Johannes Rabie',
                                  slug='petrus-johannes-rabie'),
            # Ms L L VAN DER MERWE
            Person.objects.create(title='Ms',
                                  legal_name='Lilian Luca van der Merwe',
                                  slug='lilian-luca-van-der-merwe'),
            # Mr M S F DE FREITAS
            Person.objects.create(title='Mr',
                                  legal_name='Mario Steven Foster DE FREITAS',
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

        # TODO: create the below XML file as a "Source" instead
        an = ImportZAAkomaNtoso(instance=self.instance, commit=True)
        section = an.import_document(document_path)

        self.assertTrue(section is not None,
                        'Hansard should be parsed into a non-null section.')

        # Get all the detected speakers from the speeches in the hansard
        detected_speakers = set()
        for section in section.children.all():
            for speech in section.speech_set.all():
                detected_speakers.add(speech.speaker)

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
