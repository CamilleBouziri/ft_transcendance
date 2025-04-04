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
    # player1_is_playing = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.player1.nom} vs {self.player2}"


class MorpionMatch(models.Model):
    STATUS_CHOICES = [
        ("waiting", "Waiting for player"),
        ("in_progress", "In Progress"),
        ("finished", "Finished"),
    ]

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_morpion_matches"
    )
    players = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="morpion_matches",
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="waiting"
    )
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="won_morpion_matches",
        null=True,
        blank=True
    )
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='initiated_morpion_matches',
        null=True
    )

    def is_full(self):
        return self.players.count() == 2

    def can_start(self):
        return self.is_full() and self.status == "waiting"