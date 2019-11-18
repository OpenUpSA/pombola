# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('za_hansard', '0007_auto_20191118_1206'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='pmg_id',
            field=models.IntegerField(null=True),
        ),
    ]
