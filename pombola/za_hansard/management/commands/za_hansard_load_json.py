from __future__ import absolute_import
from speeches.management.import_commands import ImportCommand
from pombola.za_hansard.importers.import_json import ImportJson


class Command(ImportCommand):
    importer_class = ImportJson
    document_extension = 'txt'
