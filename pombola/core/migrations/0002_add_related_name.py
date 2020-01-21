# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='identifier',
            name='content_type',
            field=models.ForeignKey(related_name='pombola_identifier_set', to='contenttypes.ContentType'),
            preserve_default=True,
        ),
    ]
