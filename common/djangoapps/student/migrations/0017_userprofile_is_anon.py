# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2020-04-24 16:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0016_coursenrollment_course_on_delete_do_nothing'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='is_anon',
            field=models.BooleanField(default=0, verbose_name=b'Is Anonymous'),
        ),
    ]
