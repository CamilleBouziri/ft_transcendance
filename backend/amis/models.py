from django.db import models
from auth_app.models import Utilisateurs


class Ami(models.Model):

    utilisateur = models.ForeignKey(Utilisateurs, related_name='demandes_envoyees', on_delete=models.CASCADE)

    ami = models.ForeignKey(Utilisateurs, related_name='demandes_recues', on_delete=models.CASCADE)
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('accepte', 'Accepté'),
        ('refuse', 'Refusé'),
    ]

    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='en_attente')
    
    date_ajout = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.utilisateur} - {self.ami} ({self.get_statut_display()})"