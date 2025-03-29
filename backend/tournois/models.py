from django.db import models
from django.conf import settings  # Récupération du modèle utilisateur personnalisé

class Tournoi(models.Model):
    STATUT_CHOICES = [
        ("en_attente", "Attente"),
        ("en_cours", "En cours"),
        ("termine", "Terminé"),
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
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    def est_complet(self):
        """Vérifie si le tournoi a bien 4 joueurs."""
        return self.joueurs.count() == 4

    def mettre_a_jour_tournoi(self):
        """Gère la progression du tournoi et crée le prochain match automatiquement."""
        matchs = list(self.matchs.all().order_by("round"))

        # Vérifier si la finale doit être créée
        if len(matchs) == 2 and all(m.gagnant for m in matchs):
            Match.objects.create(
                tournoi=self,
                joueur1=matchs[0].gagnant,
                joueur2=matchs[1].gagnant,
                round="finale"
            )
        
        # Vérifier si le tournoi est terminé
        elif len(matchs) == 3 and matchs[2].gagnant:
            self.gagnant_final = matchs[2].gagnant
            self.statut = "termine"
            self.save()
            self.mettre_a_jour_classement()

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
    score_joueur1 = models.IntegerField(default=0, verbose_name="Score Joueur 1")
    score_joueur2 = models.IntegerField(default=0, verbose_name="Score Joueur 2")
    round = models.CharField(
        max_length=20,
        choices=ROUND_CHOICES,
        default="demi_finale",
        verbose_name="Phase du match",
    )
    date_match = models.DateTimeField(auto_now_add=True, verbose_name="Date du match")

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
