# Generated by Django 5.2.1 on 2025-05-25 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0004_uploadedfile_vt_result_uploadedfile_vt_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadedfile',
            name='vt_status',
            field=models.CharField(default='not_started', max_length=20),
        ),
    ]
