# Generated by Django 4.2 on 2025-03-31 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='player1_is_playing',
            field=models.BooleanField(default=False),
        ),
    ]
