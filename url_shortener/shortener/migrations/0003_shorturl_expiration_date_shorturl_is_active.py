# Generated by Django 5.1.5 on 2025-03-28 17:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shortener', '0002_clickevent'),
    ]

    operations = [
        migrations.AddField(
            model_name='shorturl',
            name='expiration_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='shorturl',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
