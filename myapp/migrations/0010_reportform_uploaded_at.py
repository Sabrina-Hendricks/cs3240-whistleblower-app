# Generated by Django 5.0.3 on 2024-04-08 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0009_reportform_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportform',
            name='uploaded_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
