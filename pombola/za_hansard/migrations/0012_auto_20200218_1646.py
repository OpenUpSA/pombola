# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('za_hansard', '0011_auto_20200218_1642'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='answer',
            unique_together=set([('written_number', 'house', 'year', 'term'), ('oral_number', 'house', 'year', 'term'), ('dp_number', 'house', 'year', 'term'), ('president_number', 'house', 'year', 'term')]),
        ),
        migrations.AlterUniqueTogether(
            name='question',
            unique_together=set([('written_number', 'house', 'year', 'term'), ('oral_number', 'house', 'year', 'term'), ('dp_number', 'house', 'year', 'term'), ('president_number', 'house', 'year', 'term')]),
        ),
    ]
