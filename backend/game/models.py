from django.db import models

from django.conf import settings
from django.db import models

class Game(models.Model):
    name = models.CharField(max_length=100, default="Pong Match")
    player1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Référence dynamique à ton modèle Utilisateurs
        on_delete=models.CASCADE,
        related_name="games_as_player1"
    )
    player2 = models.CharField(max_length=50, default="Player 2")  # Opposant générique
    winner = models.CharField(max_length=50, null=True, blank=True)  # Nom du gagnant
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.player1.nom} vs {self.player2}"


