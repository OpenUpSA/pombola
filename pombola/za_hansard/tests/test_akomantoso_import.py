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
logging.disable(logging.WARNING)


class ImportZAAkomaNtosoTests(InstanceTestCase):
    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 'test_inputs',
            'hansard')
        super(ImportZAAkomaNtosoTests, cls).setUpClass()
        call_command('update_index', interactive=False, verbosity=3)
        recreate_entities()

    def test_import(self):
        document_path = os.path.join(self._in_fixtures, 'NA200912.xml')

        # Create Persons to identify
        NUM_PERSONS = 2
        Person.objects.create(title='Mr',
                              legal_name='Mario Steven Foster DE FREITAS',
                              slug='mario-steven-foster-de-freitas')
        Person.objects.create(title='Ms',
                              legal_name='Agnes Christin Mashishi',
                              slug='agnes-christin-mashishi')

        # Create Speakers for the persons
        call_command('pombola_sayit_sync_pombola_to_popolo')
        self.assertNotEqual(0, PombolaSayItJoin.objects.count(),
                            'Speakers should be linked to persons.')

        # Create EntityName objects
        call_command('popolo_name_resolver_init')
        self.assertNotEqual(0, EntityName.objects.count(),
                            'EntityNames should be created for speakers.')

        # TODO: create the below XML file as a "Source" instead
        an = ImportZAAkomaNtoso(instance=self.instance, commit=True)
        section = an.import_document(document_path)

        self.assertTrue(section is not None,
                        'Hansard should be parsed into a non-null section.')

        # Check that all the sections have correct looking titles
        for sub in section.children.all():
            self.assertFalse("Member'S" in sub.title)

        # Check that the speakers were linked correctly to the above created Persons
        speakers = Speaker.objects.all()

        def linked_to_person(speaker):
            try:
                return speaker.pombola_link.pombola_person is not None
            except PombolaSayItJoin.DoesNotExist:
                return False

        THRESHOLD = 48

        resolved = filter(linked_to_person, speakers)
        for resolved_speaker in resolved:
            logging.info(resolved_speaker.name)

        self.assertTrue(
            len(resolved) == NUM_PERSONS,
            "%d speakers identified out of %d, but %d should have been identified"
            % (len(resolved), len(speakers), NUM_PERSONS))

        self.assertTrue(False)

    # def test_title_casing(self):
    #     tests = (
    #         # initial, expected
    #         ("ALL CAPS", "All Caps"),
    #         ("MEMBER'S Statement", "Member's Statement"),
    #         ("member’s", "Member’s"),
    #     )

    #     for initial, expected in tests:
    #         self.assertEqual(title_case_heading(initial), expected)
