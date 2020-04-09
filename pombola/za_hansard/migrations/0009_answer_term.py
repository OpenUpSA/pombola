# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('south_africa', '0005_create_parliamentary_terms'),
        ('za_hansard', '0008_auto_20200218_1632'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='term',
            field=models.ForeignKey(to='south_africa.ParliamentaryTerm', null=True),
        ),
    ]
