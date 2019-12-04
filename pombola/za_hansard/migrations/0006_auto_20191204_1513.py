# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('za_hansard', '0005_auto_20191118_1243'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sourceparsinglog',
            name='date',
        ),
        migrations.AddField(
            model_name='sourceparsinglog',
            name='created',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='sourceparsinglog',
            name='updated',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
