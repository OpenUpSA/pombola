# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from pombola.south_africa.models import ParliamentaryTerm
from pombola.za_hansard.models import Answer


def forwards_func(apps, schema_editor):
    # For every Answer, calculate it's term
    for answer in Answer.objects.all():
        try:
            term = ParliamentaryTerm.get_term_from_date(answer.date)
            answer.term = term
            answer.save()
        except ParliamentaryTerm.DoesNotExist: 
            raise Exception(
                "Unable to calculate term for Answer with ID %d. Please "
                "check that a ParliamentaryTerm exists that includes this date: "
                "%s."
                % (answer.id, answer.date))

def reverse_func(apps, schema_editor):
    # Ignore
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('za_hansard', '0009_answer_term'),
    ]
    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]

