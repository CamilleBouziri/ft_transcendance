from django.db import models
from django.conf import settings  # Récupération du modèle utilisateur personnalisé
from django.utils.translation import gettext_lazy as _

class Tournoi(models.Model):
    STATUT_CHOICES = [
        ("en_attente", _("Waiting")),
        ("en_cours", _("In Progress")),
        ("termine", _("Finished")),
    ]

    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom du tournoi")
    createur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tournois_crees",
        verbose_name="Créateur",
    )
    joueurs = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="tournois",
        blank=True,
        verbose_name="Joueurs",
    )
    gagnant_final = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tournois_gagnes",
        null=True,
        blank=True,
        verbose_name="Gagnant du tournoi",
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="en_attente",
        verbose_name="Statut",
    )
    joueurs_noms_personnalises = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Noms personnalisés des joueurs"
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    def est_complet(self):
        """Vérifie si le tournoi a bien 4 joueurs."""
        return self.joueurs.count() == 4

    def mettre_a_jour_tournoi(self):
        """Gère la progression du tournoi et crée le match final automatiquement."""
        matchs = list(self.matchs.all().order_by("ordre"))

        # Vérifier si les deux premiers matchs sont terminés
        if len(matchs) == 2 and matchs[0].gagnant and matchs[1].gagnant:
            # Créer le match final s'il n'existe pas déjà
            if not Match.objects.filter(tournoi=self, round="finale").exists():
                Match.objects.create(
                    tournoi=self,
                    joueur1=matchs[0].gagnant,
                    joueur2=matchs[1].gagnant,
                    round="finale",
                    ordre=2
                )
        # Vérifier si le tournoi est terminé
        finale = Match.objects.filter(tournoi=self, round="finale").first()
        if finale and finale.gagnant:
            self.gagnant_final = finale.gagnant
            self.statut = "termine"
            self.save()
    def mettre_a_jour_classement(self):
        """Met à jour le classement des joueurs selon leurs performances."""
        classement = []
        matchs = list(self.matchs.all())
        # 1er = Gagnant de la finale
        if self.gagnant_final:
            classement.append(self.gagnant_final)
        # 2ème = Perdant de la finale
        finale = matchs[2] if len(matchs) == 3 else None
        if finale and finale.joueur1 != finale.gagnant:
            classement.append(finale.joueur1)
        elif finale and finale.joueur2 != finale.gagnant:
            classement.append(finale.joueur2)
        # 3ème et 4ème = Perdants des demi-finales
        for match in matchs[:2]:  # Premier tour (demi-finales)
            if match.joueur1 != match.gagnant:
                classement.append(match.joueur1)
            if match.joueur2 != match.gagnant:
                classement.append(match.joueur2)
        # Sauvegarde du classement (1er = 3 pts, 2e = 2 pts, etc.)
        for i, joueur in enumerate(classement):
            Classement.objects.create(tournoi=self, joueur=joueur, points=(3 - i))
    def __str__(self):
        return f"{self.nom} ({self.get_statut_display()})"


class Match(models.Model):
    ROUND_CHOICES = [
        ("demi_finale", "Demi-finale"),
        ("finale", "Finale"),
    ]

    tournoi = models.ForeignKey(
        Tournoi,
        on_delete=models.CASCADE,
        related_name="matchs",
        verbose_name="Tournoi",
    )
    joueur1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="matchs_joueur1",
        verbose_name="Joueur 1",
    )
    joueur2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="matchs_joueur2",
        verbose_name="Joueur 2",
    )
    gagnant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="matchs_gagnes",
        null=True,
        blank=True,
        verbose_name="Gagnant",
    )
    gagnant_nom = models.CharField(
    max_length=100, 
    blank=True, 
    verbose_name="Nom personnalisé du gagnant",
    )

    score_joueur1 = models.IntegerField(default=0, verbose_name="Score Joueur 1")
    score_joueur2 = models.IntegerField(default=0, verbose_name="Score Joueur 2")
    round = models.CharField(
        max_length=20,
        choices=ROUND_CHOICES,
        default="demi_finale",
        verbose_name="Phase du match",
    )
    date_match = models.DateTimeField(auto_now_add=True, verbose_name="Date du match")
    ordre = models.IntegerField(default=0, verbose_name="Ordre du match")
    joueur1_nom = models.CharField(max_length=100, blank=True, verbose_name="Nom personnalisé Joueur 1")
    joueur2_nom = models.CharField(max_length=100, blank=True, verbose_name="Nom personnalisé Joueur 2")

    class Meta:
        ordering = ['ordre']  # Tri par défaut selon l'ordre

    def save(self, *args, **kwargs):
        # Remplir les noms personnalisés si non définis
        if not self.joueur1_nom and self.joueur1:
            self.joueur1_nom = self.tournoi.joueurs_noms_personnalises.get(str(self.joueur1.id), self.joueur1.nom)
        if not self.joueur2_nom and self.joueur2:
            self.joueur2_nom = self.tournoi.joueurs_noms_personnalises.get(str(self.joueur2.id), self.joueur2.nom)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Match: {self.joueur1} vs {self.joueur2} ({self.tournoi.nom})"


class Classement(models.Model):
    tournoi = models.ForeignKey(
        Tournoi,
        on_delete=models.CASCADE,
        related_name="classements",
        verbose_name="Tournoi"
    )
    joueur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Joueur"
    )
    points = models.IntegerField(default=0, verbose_name="Points")

    def __str__(self):
        return f"{self.joueur.nom} - {self.points} points ({self.tournoi.nom})"
