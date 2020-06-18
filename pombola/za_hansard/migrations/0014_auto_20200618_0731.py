# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('za_hansard', '0013_auto_20200327_1633'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='sayit_section',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, blank=True, to='speeches.Section', help_text=b'Associated Sayit section object, if imported'),
        ),
    ]
