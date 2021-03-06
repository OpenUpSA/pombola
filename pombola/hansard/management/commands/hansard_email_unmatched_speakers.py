from django.core.management.base import BaseCommand
from django.core.mail import send_mail

from pombola.hansard.models import Alias


class Command(BaseCommand):
    help = 'Email a list of all the speaker names that have not been matched up to a real person'

    def handle(self, **options):
        unassigned = Alias.objects.unassigned()
        count = unassigned.count()

        if count is 0:
            return

        body = []
        body.append("There are {} Hansard speaker names that could not be matched to a person\n".format(count))
        body.append("Please go to http://info.mzalendo.com/admin/hansard/alias/ to update list\n")
        for alias in unassigned:
            body.append(u"\t'{}'".format(alias.alias))

        send_mail(
            '[Hansard] Unmatched speaker names report',
            '\n'.join(body),
            'no-reply@info.mzalendo.com',
            ['mzalendo-managers@mysociety.org'],
        )
