# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('south_africa', '0005_create_parliamentary_terms'),
        ('za_hansard', '0005_auto_20200110_1047'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='term',
            field=models.ForeignKey(to='south_africa.ParliamentaryTerm', null=True),
        ),
    ]
