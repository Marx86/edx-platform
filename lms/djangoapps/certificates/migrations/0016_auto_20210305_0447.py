# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2021-03-05 09:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0015_auto_20210304_0425'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='certificatetemplate',
            name='organization',
        ),
        migrations.AddField(
            model_name='certificatetemplate',
            name='organization_name',
            field=models.CharField(blank=True, help_text='Organization name of template. Used if organization id is not set.', max_length=255, null=True),
        ),
    ]
