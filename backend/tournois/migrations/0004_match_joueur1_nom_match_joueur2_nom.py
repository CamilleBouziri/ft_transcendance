# Generated by Django 4.2 on 2025-04-03 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournois', '0003_alter_match_options_match_ordre'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='joueur1_nom',
            field=models.CharField(blank=True, max_length=100, verbose_name='Nom personnalisé Joueur 1'),
        ),
        migrations.AddField(
            model_name='match',
            name='joueur2_nom',
            field=models.CharField(blank=True, max_length=100, verbose_name='Nom personnalisé Joueur 2'),
        ),
    ]
