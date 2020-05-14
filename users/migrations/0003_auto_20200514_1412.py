# Generated by Django 3.0.6 on 2020-05-14 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20200513_1501'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='email address'),
        ),
        migrations.AlterField(
            model_name='user',
            name='student_number',
            field=models.CharField(max_length=8, unique=True, verbose_name='student number'),
        ),
    ]
