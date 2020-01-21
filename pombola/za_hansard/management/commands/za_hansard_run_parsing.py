
# This script changed extensively when the Kenyan Parliament website changed after the 2013 Election.
#
# The previous version can be seen at:
#
#    https://github.com/mysociety/mzalendo/blob/7181e30519b140229e3817786e4a7440ac08288d/mzalendo/hansard/management/commands/hansard_check_for_new_sources.py

from __future__ import absolute_import
import pprint
import httplib2
import re
import datetime
import time
import sys

from bs4 import BeautifulSoup
from lxml import etree

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from pombola.za_hansard.models import Source, SourceUrlCouldNotBeRetrieved, SourceParsingLog
from pombola.za_hansard.parse import ZAHansardParser, ConversionException, DateParseException
import six


class Command(BaseCommand):
    help = 'Parse unparsed'
    option_list = BaseCommand.option_list + (
        make_option('--redo',
                    default=False,
                    action='store_true',
                    help='Redo already completed parses',
                    ),
        make_option('--id',
                    type='str',
                    help='Parse a given id',
                    ),
        make_option('--retry',
                    default=False,
                    action='store_true',
                    help='Retry attempted (but not completed) parses',
                    ),
        make_option('--since',
                    help='Oldest date to parse Sources from (format must be YYYY-MM-DD).',
                    ),
        make_option('--retry-download',
                    default=False,
                    action='store_true',
                    help='Retry download of previously 404\'d documents',
                    ),
        make_option('--limit',
                    default=0,
                    type='int',
                    help='limit query (default 0 for none)',
                    ),
    )

    def handle(self, *args, **options):
        limit = options['limit']

        if options['id']:
            sources = Source.objects.filter(id=options['id'])
        else:
            sources = Source.objects.all()
            if options['since']:
                try:
                    since_date = datetime.datetime.strptime(options['since'], "%Y-%m-%d")
                    sources = sources.filter(date__gte=since_date)
                except ValueError:
                    self.stderr.write(u"Since date must be in the format YYYY-MM-DD, e.g. 2019-12-04.")
                    sys.exit(-1)
            if options['redo']:
                if not options['retry_download']:
                    sources = sources.filter(is404=False)
                else:
                    self.stdout.write(u"retry_download")
            elif options['retry']:
                sources = sources.requires_completion(
                    options['retry_download'])
            else:
                sources = sources.requires_processing()

        sources.defer('xml')
        for s in (sources[:limit] if limit else sources):
            parsing_log = SourceParsingLog(source=s, log="Starting to parse source...\n")
            if s.language != 'English' and s.language != 'ENG':
                parsing_log.log += "Source language is not English. Skipping source.\n"
                continue
            s.last_processing_attempt = datetime.datetime.now().date()
            s.save()
            try:
                try:
                    filename = s.file()
                except SourceUrlCouldNotBeRetrieved as e:
                    parsing_log.log += "Source url returned a 404 error. Source could not be retreived. Skipping source.\n"
                    s.is404 = True
                    s.save()
                    raise e
                obj = ZAHansardParser.parse(filename)
                xml = etree.tostring(obj.akomaNtoso)
                parsing_log.log += "Source successfully parsed. Writing to parsed data to xml file...\n"
                s.last_processing_success = datetime.datetime.now().date()

                open('%s.xml' % filename, 'w').write(xml)
                s.save()
                parsing_log.log += "Saved parsed data in xml file at %s.xml.\n" % filename
                parsing_log.success = True
                self.stdout.write(u"Processed {} ({})\n".format(
                                  s.document_name, s.document_number))
            except Exception as e:
                parsing_log.log += u"Error '%s' occurred while parsing source.\n" % e
                parsing_log.error = type(e).__name__
                parsing_log.success = False
                self.stderr.write(u"WARN: Failed to run parsing for %s: %s" % (s.id, six.text_type(e)))

            parsing_log.save()
