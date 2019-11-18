# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('za_hansard', '0005_zahansardparsinglog'),
    ]

    operations = [
        migrations.AddField(
            model_name='zahansardparsinglog',
            name='success',
            field=models.BooleanField(default=False),
        ),
    ]
