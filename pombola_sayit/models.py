from django.db import models

from pombola.core.models import Person
from speeches.models import Speaker


class PombolaSayItJoin(models.Model):

    """This model provides a join table between Pombola and SsayIt people"""

    pombola_person = models.OneToOneField(Person, related_name='sayit_link', on_delete=models.CASCADE)
    sayit_speaker = models.OneToOneField(Speaker, related_name='pombola_link', on_delete=models.CASCADE)
