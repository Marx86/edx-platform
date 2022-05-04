# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2022-05-03 12:39
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tedix_ro', '0018_auto_20210812_1132'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='parent_phone',
            field=models.CharField(max_length=15, null=True, validators=[django.core.validators.RegexValidator(message='The phone number length must be from 10 to 15 digits.', regex=b'^\\d{10,15}$')]),
        ),
    ]
