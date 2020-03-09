# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('south_africa', '0005_create_parliamentary_terms'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parliamentaryterm',
            name='number',
            field=models.IntegerField(help_text=b'e.g. 25 for the 25th parliament', serialize=False, primary_key=True),
        ),
    ]
