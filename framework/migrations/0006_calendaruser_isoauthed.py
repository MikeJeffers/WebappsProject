# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-04-07 21:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('framework', '0005_appsettings_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='calendaruser',
            name='isOAuthed',
            field=models.BooleanField(default=False),
        ),
    ]
