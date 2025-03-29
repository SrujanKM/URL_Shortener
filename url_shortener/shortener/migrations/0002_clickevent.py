# Generated by Django 5.1.5 on 2025-03-28 14:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shortener', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClickEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.CharField(max_length=255)),
                ('referrer', models.URLField(blank=True, null=True)),
                ('short_url', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='clicks', to='shortener.shorturl')),
            ],
        ),
    ]
