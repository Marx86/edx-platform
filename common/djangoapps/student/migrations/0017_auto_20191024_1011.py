# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-10-24 14:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0016_coursenrollment_course_on_delete_do_nothing'),
    ]

    operations = [
        migrations.CreateModel(
            name='Position',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=120, null=True)),
                ('has_specialization', models.BooleanField(default=False)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='student.Position')),
            ],
        ),
        migrations.CreateModel(
            name='Specialization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='userprofile',
            name='additional_email',
            field=models.EmailField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='date_of_birth',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='other_position',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='phone',
            field=models.CharField(blank=True, max_length=13, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='region',
            field=models.CharField(blank=True, choices=[(b'crimea', '\u0410\u0432\u0442\u043e\u043d\u043e\u043c\u043d\u0430 \u0420\u0435\u0441\u043f\u0443\u0431\u043b\u0456\u043a\u0430 \u041a\u0440\u0438\u043c'), (b'vinnitskaya', '\u0412\u0456\u043d\u043d\u0438\u0446\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'volinskaya', '\u0412\u043e\u043b\u0438\u043d\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'dnepropetrovskaya', '\u0414\u043d\u0456\u043f\u0440\u043e\u043f\u0435\u0442\u0440\u043e\u0432\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'donetskaya', '\u0414\u043e\u043d\u0435\u0446\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'zitomirskaya', '\u0416\u0438\u0442\u043e\u043c\u0438\u0440\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'zakarpatskaya', '\u0417\u0430\u043a\u0430\u0440\u043f\u0430\u0442\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'zaporozskaya', '\u0417\u0430\u043f\u043e\u0440\u0456\u0437\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'ivano-frankovskaya', '\u0406\u0432\u0430\u043d\u043e-\u0424\u0440\u0430\u043d\u043a\u0456\u0432\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'kievskaya', '\u041a\u0438\u0457\u0432\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'kirovogradskaya', '\u041a\u0456\u0440\u043e\u0432\u043e\u0433\u0440\u0430\u0434\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'luganskaya', '\u041b\u0443\u0433\u0430\u043d\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'lvovskaya', '\u041b\u044c\u0432\u0456\u0432\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'nikolaevskaya', '\u041c\u0438\u043a\u043e\u043b\u0430\u0457\u0432\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'odesskaya', '\u041e\u0434\u0435\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'poltavskaya', '\u041f\u043e\u043b\u0442\u0430\u0432\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'rovenskaya', '\u0420\u0456\u0432\u043d\u0435\u043d\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'sumskaya', '\u0421\u0443\u043c\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'ternopolskaya', '\u0422\u0435\u0440\u043d\u043e\u043f\u0456\u043b\u044c\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'kharkovskaya', '\u0425\u0430\u0440\u043a\u0456\u0432\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'khersonskaya', '\u0425\u0435\u0440\u0441\u043e\u043d\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'khmelnitskaya', '\u0425\u043c\u0435\u043b\u044c\u043d\u0438\u0446\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'cherkasskaya', '\u0427\u0435\u0440\u043a\u0430\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'chernovetskaya', '\u0427\u0435\u0440\u043d\u0456\u0432\u0435\u0446\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c'), (b'chernigovskaya', '\u0427\u0435\u0440\u043d\u0456\u0433\u0456\u0432\u0441\u044c\u043a\u0430 \u043e\u0431\u043b\u0430\u0441\u0442\u044c')], max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='second_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='gender',
            field=models.CharField(blank=True, choices=[(b'm', b'Male'), (b'f', b'Female')], db_index=True, max_length=6, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='position',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='student.Position'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='specialization',
            field=models.ManyToManyField(to='student.Specialization'),
        ),
    ]
