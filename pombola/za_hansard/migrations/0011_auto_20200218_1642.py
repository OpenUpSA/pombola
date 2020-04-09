# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('za_hansard', '0010_create_terms_for_answers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='term',
            field=models.ForeignKey(to='south_africa.ParliamentaryTerm'),
        ),
    ]
