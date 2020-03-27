# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('za_hansard', '0012_auto_20200218_1646'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionParsingError',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('pmg_url', models.URLField()),
                ('last_seen', models.DateTimeField()),
                ('error_type', models.CharField(max_length=20)),
                ('error_message', models.CharField(max_length=300)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='questionparsingerror',
            unique_together=set([('pmg_url', 'error_type')]),
        ),
    ]
