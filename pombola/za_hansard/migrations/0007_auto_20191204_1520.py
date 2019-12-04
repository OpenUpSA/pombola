# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('za_hansard', '0006_auto_20191204_1513'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sourceparsinglog',
            name='source',
            field=models.OneToOneField(null=True, to='za_hansard.Source'),
        ),
    ]
