# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_auto_20190906_1342'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganisationHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('new_organisation', models.ForeignKey(related_name='org_history_new', blank=True, to='core.Organisation', null=True)),
                ('old_organisation', models.ForeignKey(related_name='org_history_old', to='core.Organisation')),
            ],
        ),
    ]
