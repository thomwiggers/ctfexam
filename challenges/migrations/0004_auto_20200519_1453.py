# Generated by Django 3.0.6 on 2020-05-19 12:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0003_auto_20200514_1559'),
    ]

    operations = [
        migrations.AddField(
            model_name='challengeprocess',
            name='port',
            field=models.PositiveSmallIntegerField(default=1000),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='challengeprocess',
            name='process_identifier',
            field=models.TextField(default='test'),
            preserve_default=False,
        ),
    ]
