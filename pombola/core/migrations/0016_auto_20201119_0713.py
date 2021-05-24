# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_organisationhistory'),
    ]

    operations = [
        migrations.RenameField(
            model_name='organisationhistory',
            old_name='date',
            new_name='date_changed',
        ),
        migrations.AddField(
            model_name='organisationhistory',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2020, 11, 19, 7, 12, 39, 276251), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='organisationhistory',
            name='updated',
            field=models.DateTimeField(default=datetime.datetime(2020, 11, 19, 7, 13, 2, 607518), auto_now=True),
            preserve_default=False,
        ),
    ]
