# This command creates a new PopIt instance based on the Person,
# Position and Organisation models in Pombola.

import json
from optparse import make_option
from os.path import exists, isdir, join
from urllib.parse import urlparse

from pombola.core.popolo import get_popolo_data

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    # args = 'OUTPUT-DIRECTORY POMBOLA-URL'
    help = 'Export all people, organisations and memberships to Popolo JSON and mongoexport format'

    def add_arguments(self, parser):
        parser.add_argument('OUTPUT-DIRECTORY')
        parser.add_argument('POMBOLA-URL')
        parser.add_argument(
            "--pombola",
            dest="pombola",
            action="store_true",
            help="Make a single file with inline memberships"
        )

    def handle(self, *args, **options):
        output_directory = options['OUTPUT-DIRECTORY']
        pombola_url = options['POMBOLA-URL']
        if not (exists(output_directory) and isdir(output_directory)):
            message = "'{0}' was not a directory"
            raise CommandError(message.format(output_directory))
        parsed_url = urlparse(pombola_url)
        if not parsed_url.netloc:
            message = "The Pombola URL must begin http:// or https://"
            raise CommandError(message)

        primary_id_scheme = '.'.join(reversed(parsed_url.netloc.split('.')))

        if options['pombola']:
            for inline_memberships, leafname in (
                    (True, 'pombola.json'),
                    (False, 'pombola-no-inline-memberships.json'),
            ):
                popolo_data = get_popolo_data(
                    primary_id_scheme,
                    pombola_url,
                    inline_memberships=inline_memberships
                )
                output_filename = join(output_directory, leafname)
                with open(output_filename, 'w') as f:
                    json.dump(popolo_data, f, indent=4, sort_keys=True)
        else:
            popolo_data = get_popolo_data(
                primary_id_scheme,
                pombola_url,
                inline_memberships=False
            )
            for collection, data in popolo_data.items():
                for mongoexport_format in (True, False):
                    if mongoexport_format:
                        output_basename = 'mongo-' + collection + '.dump'
                    else:
                        output_basename = collection + ".json"
                    output_filename = join(output_directory, output_basename)
                    with open(output_filename, 'w') as f:
                        if mongoexport_format:
                            for item in data:
                                item['_id'] = item['id']
                                json.dump(item, f, sort_keys=True)
                                f.write("\n")
                        else:
                            json.dump(data, f, indent=4, sort_keys=True)
