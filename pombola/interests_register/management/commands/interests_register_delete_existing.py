from django.core.management.base import BaseCommand
from ...models import Release, Category, Entry, EntryLineItem


class Command(BaseCommand):
    help = 'Delete existing declarations of members interests - allows for subsequent re-importing of data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--commit',
            action='store_true',
            dest='commit',
            help='Actually update the database')

    def handle(self, **options):
        count_releases = Release.objects.count()
        count_categories = Category.objects.count()
        count_entries = Entry.objects.count()
        count_entrylineitems = EntryLineItem.objects.count()

        print "  Deleting", count_releases, "releases"
        print "  Deleting", count_categories, "categories"
        print "  Deleting", count_entries, "entries"
        print "  Deleting", count_entrylineitems, "entrylineitems\n"

        if options['commit']:
            print "  Executing the delete"
            Release.objects.all().delete()
            Category.objects.all().delete()
        else:
            print "  Not executing the delete (--commit not specified)"
