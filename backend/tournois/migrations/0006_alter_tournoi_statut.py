# Generated by Django 4.2 on 2025-04-06 13:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournois', '0005_match_gagnant_nom'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tournoi',
            name='statut',
            field=models.CharField(choices=[('en_attente', 'Waiting'), ('en_cours', 'In Progress'), ('termine', 'Finished')], default='en_attente', max_length=20, verbose_name='Statut'),
        ),
    ]
