from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver

@receiver(user_logged_out)
def set_user_offline(sender, request, user, **kwargs):
    if user.is_authenticated:
        user.is_online = False  # Marque l'utilisateur comme hors ligne
        user.save()