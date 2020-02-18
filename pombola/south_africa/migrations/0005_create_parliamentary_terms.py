# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date
from django.db import migrations, models

from pombola.south_africa.models import ParliamentaryTerm

TERMS = [
    ParliamentaryTerm(number=25, start_date=date(2009, 6, 1), end_date=date(2014, 5, 31)),
    ParliamentaryTerm(number=26, start_date=date(2014, 6, 1), end_date=date(2019, 5, 31)),
    ParliamentaryTerm(number=27, start_date=date(2019, 6, 1), end_date=date(2024, 5, 31)),
    ParliamentaryTerm(number=28, start_date=date(2024, 6, 1), end_date=date(2029, 5, 31))
]

def create_parliaments(apps, schema_editor):
    ParliamentaryTerm.objects.bulk_create(TERMS)

def delete_parliaments(apps, schema_editor):
    for term in TERMS:
        term.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('south_africa', '0004_parliamentaryterm'),
    ]

    operations = [
        migrations.RunPython(create_parliaments, delete_parliaments),
    ]
