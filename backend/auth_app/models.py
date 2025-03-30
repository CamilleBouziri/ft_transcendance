
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class UtilisateursManager(BaseUserManager):
    def create_user(self, nom, email=None, password=None):
        if not nom:
            raise ValueError("Le champ 'nom' est obligatoire.")
        user = self.model(nom=nom, email=self.normalize_email(email))
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, nom, email=None, password=None):
        user = self.create_user(nom=nom, email=email, password=password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class Utilisateurs(AbstractBaseUser):
    nom = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)  # Champ email ajouté
    photo_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    # Champs pour les victoires et défaites
    wins = models.PositiveIntegerField(default=0)  # Victoires
    losses = models.PositiveIntegerField(default=0)  # Défaites
    objects = UtilisateursManager()

    USERNAME_FIELD = 'nom'
    REQUIRED_FIELDS = ['email']  # Ajoutez email comme champ requis


    # Méthodes nécessaires pour l'administration Django
    def has_perm(self, perm, obj=None):
        """
        Retourne True si l'utilisateur a une permission spécifique.
        Ici, tous les superutilisateurs ont toutes les permissions.
        """
        return self.is_superuser

    def has_module_perms(self, app_label):
        """
        Retourne True si l'utilisateur a des permissions pour le module spécifié.
        Ici, tous les superutilisateurs ont accès à tous les modules.
        """
        return self.is_superuser

from django.contrib.auth.models import User
