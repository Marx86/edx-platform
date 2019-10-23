# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-10-16 13:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0016_coursenrollment_course_on_delete_do_nothing'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=120, null=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='student.Role')),
            ],
        ),
        migrations.AddField(
            model_name='userprofile',
            name='other_role',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='role',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='student.Role'),
        ),
    ]
