# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('za_hansard', '0007_create_terms_for_questions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='term',
            field=models.ForeignKey(to='south_africa.ParliamentaryTerm'),
        ),
    ]
