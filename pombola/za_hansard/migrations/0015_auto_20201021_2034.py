# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('za_hansard', '0014_auto_20201021_2033'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='answer',
            unique_together=set([('president_number', 'house', 'date'), ('oral_number', 'house', 'date'), ('written_number', 'house', 'date'), ('dp_number', 'house', 'date')]),
        ),
    ]
