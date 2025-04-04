from django.db import models
from auth_app.models import Utilisateurs
from django.conf import settings

class Room(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Utilisateurs, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_last_message(self):
        """Récupère le dernier message de la salle."""
        return self.messages.order_by('-timestamp').first()
    
    def get_other_user_name(self, current_user):
        """Récupère le nom de l'autre utilisateur dans une conversation privée."""
        if self.name.startswith('private_'):
            room_name_parts = self.name.replace('private_', '').split('_')
            return room_name_parts[1] if room_name_parts[0] == current_user.nom else room_name_parts[0]
        return None

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(Utilisateurs, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    MESSAGE_TYPES = [
        ('text', 'Message texte'),
        ('game_invite', 'Invitation à jouer')
    ]
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    game_data = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.user.nom}: {self.content[:50]}"


class UserBlock(models.Model):
    blocker = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_blocks', on_delete=models.CASCADE)
    blocked = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocked_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')
        
    def __str__(self):
        return f"{self.blocker.nom} a bloqué {self.blocked.nom}"