from django.db import models
from auth_app.models import Utilisateurs

"""

    Utilisateur A (utilisateur)         ---( demande d'ami )-->        Utilisateur B (ami)
                                                |
                                    statut = en_attente/accepte/refuse

    Attributs :

    │── utilisateur : ForeignKey → Utilisateurs
    │   └── L'utilisateur qui envoie la demande d'amitié
    │
    │── ami: ForeignKey → Utilisateurs
    │   └── L'utilisateur qui reçoit la demande d'amitié
    │
    │── statut : CharField 
    │   └── Valeurs possibles: 'en_attente', 'accepte', 'refuse'
    │   └── Statut actuel de la demande d'amitié
    │
    │── date_ajout : DateTimeField (auto_now_add=True)
        └── Date et heure de création de la demande d'amitié

"""

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