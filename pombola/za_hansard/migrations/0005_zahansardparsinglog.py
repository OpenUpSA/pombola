# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('za_hansard', '0004_auto_20190322_1856'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZAHansardParsingLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(auto_now_add=True)),
                ('log', models.TextField(default=b'')),
                ('error', models.CharField(default=b'', max_length=300)),
                ('source', models.ForeignKey(to='za_hansard.Source')),
            ],
        ),
    ]
