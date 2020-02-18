# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('south_africa', '0003_attendancefororganisationtoggle'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParliamentaryTerm',
            fields=[
                ('number', models.IntegerField(serialize=False, primary_key=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
            ],
        ),
    ]
