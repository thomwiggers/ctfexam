# Generated by Django 3.1.4 on 2020-12-03 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0009_auto_20201203_0934'),
    ]

    operations = [
        migrations.AddField(
            model_name='challenge',
            name='listen_ports',
            field=models.JSONField(default=1337, verbose_name='Ports exposed by this container'),
            preserve_default=False,
        ),
    ]
