# Generated by Django 3.1.2 on 2020-11-11 10:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockchain', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chain',
            name='online',
            field=models.BooleanField(default=False),
        ),
    ]
