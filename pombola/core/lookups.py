from ajax_select import LookupChannel, register
from django.db.models import Count

from .models import Person


@register('person_without_speaker')
class PersonWithoutSpeakerLookup(LookupChannel):

    model = Person

    def get_query(self, q, requests):
        return Person.objects.filter(hidden=False, legal_name__icontains=q)\
            .annotate(speakers_count=Count('sayit_link')).filter(speakers_count=0)
