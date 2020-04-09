# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from pombola.south_africa.models import ParliamentaryTerm
from pombola.za_hansard.models import Question



def forwards_func(apps, schema_editor):
    # For every Question, calculate it's term
    for question in Question.objects.all():
        try:
            term = ParliamentaryTerm.get_term_from_date(question.date)
            question.term = term
            question.save()
        except ParliamentaryTerm.DoesNotExist: 
            raise Exception(
                "Unable to calculate term for Question with ID %d. Please "
                "check that a ParliamentaryTerm exists that includes this date: "
                "%s."
                % (question.id, question.date))


def reverse_func(apps, schema_editor):
    # Ignore
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('za_hansard', '0006_question_term'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
