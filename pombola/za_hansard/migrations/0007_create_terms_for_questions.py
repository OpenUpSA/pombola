# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from pombola.south_africa.models import ParliamentaryTerm
from pombola.za_hansard.models import Question



def forwards_func(apps, schema_editor):
    # For every Question, calculate it's term
    for question in Question.objects.all():
        term = ParliamentaryTerm.get_term_from_date(question.date)
        if term:
            question.term = term
            question.save()


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
