# Generated by Django 3.1a1 on 2020-06-02 11:25

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0006_create_ports'),
    ]

    operations = [
        migrations.AddField(
            model_name='challengeprocess',
            name='started',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
