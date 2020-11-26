from django.conf import settings
from django.core.management.base import BaseCommand

from pombola.hansard.models import Entry


class Command(BaseCommand):
    help = 'Try to assign a person to each entry'
    args = ''

    def handle_noargs(self, **options):
        algorithm = settings.HANSARD_NAME_MATCHING_ALGORITHM
        Entry.assign_speakers(name_matching_algorithm=algorithm)
