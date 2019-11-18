# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('za_hansard', '0006_zahansardparsinglog_success'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zahansardparsinglog',
            name='source',
            field=models.ForeignKey(to='za_hansard.Source', null=True),
        ),
    ]
