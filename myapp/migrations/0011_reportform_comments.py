# Generated by Django 5.0.3 on 2024-04-09 23:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0010_reportform_uploaded_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportform',
            name='comments',
            field=models.TextField(default='', max_length=1000),
        ),
    ]
