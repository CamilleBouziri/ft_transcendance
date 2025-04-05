from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from random import shuffle
from django.http import JsonResponse
from .models import Tournoi, Match, Classement
from django.views.decorators.csrf import csrf_exempt


@login_required
def creer_tournoi(request):
    if request.method == "POST":
        nom = request.POST.get("nom")
        joueur_nom = request.POST.get("joueur_nom", "").strip()
        # Vérifier si le nom du tournoi existe déjà
        if Tournoi.objects.filter(nom=nom).exists():
            messages.error(request, "Un tournoi avec ce nom existe déjà.")
            return render(request, "tournois/creer_tournois.html")
        # Créer le tournoi
        tournoi = Tournoi.objects.create(nom=nom, createur=request.user)
        # Utiliser le nom personnalisé ou le nom d'utilisateur par défaut
        joueur_nom = joueur_nom if joueur_nom else request.user.nom
        # Vérifier si le nom du joueur est déjà utilisé dans ce tournoi
        if joueur_nom in tournoi.joueurs_noms_personnalises.values():
            messages.error(request, "Ce nom de joueur est déjà utilisé dans ce tournoi.")
            tournoi.delete()  # Supprimer le tournoi créé
            return render(request, "tournois/creer_tournois.html")
        # Ajouter le joueur au tournoi avec son nom personnalisé
        tournoi.joueurs_noms_personnalises[str(request.user.id)] = joueur_nom
        tournoi.save()
        tournoi.joueurs.add(request.user)
        return redirect("dashboard")
    return render(request, "tournois/creer_tournois.html")



@login_required
def rejoindre_tournoi(request, tournoi_id):
    tournoi = get_object_or_404(Tournoi, id=tournoi_id)

    if request.method == "POST":
        joueur_nom = request.POST.get("joueur_nom", "").strip()
        if tournoi.est_complet():
            messages.error(request, "Le tournoi est déjà complet.")
            return redirect("dashboard")
        if request.user in tournoi.joueurs.all():
            messages.error(request, "Vous êtes déjà inscrit à ce tournoi.")
            return redirect("dashboard")
        # Utiliser le nom personnalisé ou le nom d'utilisateur par défaut
        joueur_nom = joueur_nom if joueur_nom else request.user.nom
        # Vérifier si le nom est déjà utilisé dans ce tournoi
        if joueur_nom in tournoi.joueurs_noms_personnalises.values():
            messages.error(request, "Ce nom de joueur est déjà utilisé dans ce tournoi.")
            return render(request, "tournois/rejoindre_tournois.html", {
                "tournoi": tournoi,
                "error": "Ce nom de joueur est déjà utilisé dans ce tournoi."
            })
        # Ajouter le joueur au tournoi
        tournoi.joueurs.add(request.user)
        tournoi.joueurs_noms_personnalises[str(request.user.id)] = joueur_nom
        tournoi.save()
        return redirect("dashboard")
    return render(request, "tournois/rejoindre_tournois.html", {"tournoi": tournoi})



@login_required
def lancer_tournoi(request, tournoi_id):
    tournoi = get_object_or_404(Tournoi, id=tournoi_id)

    if tournoi.joueurs.count() != 4:
        messages.error(request, "Le tournoi doit avoir 4 joueurs pour être lancé.")
        return redirect('details_tournois', tournoi_id=tournoi.id)

    joueurs = list(tournoi.joueurs.all())

    # Création des matchs avec les noms personnalisés
    Match.objects.create(
        tournoi=tournoi,
        joueur1=joueurs[0],
        joueur2=joueurs[1],
        joueur1_nom=tournoi.joueurs_noms_personnalises.get(str(joueurs[0].id), joueurs[0].nom),
        joueur2_nom=tournoi.joueurs_noms_personnalises.get(str(joueurs[1].id), joueurs[1].nom),
        round="demi_finale",
        ordre=0
    )
    Match.objects.create(
        tournoi=tournoi,
        joueur1=joueurs[2],
        joueur2=joueurs[3],
        joueur1_nom=tournoi.joueurs_noms_personnalises.get(str(joueurs[2].id), joueurs[2].nom),
        joueur2_nom=tournoi.joueurs_noms_personnalises.get(str(joueurs[3].id), joueurs[3].nom),
        round="demi_finale",
        ordre=1
    )

    tournoi.statut = "en_cours"
    tournoi.save()

    # messages.success(request, "Le tournoi a été lancé avec succès !")
    return redirect('details_tournois', tournoi_id=tournoi.id)



from django.http import JsonResponse
import json


@login_required
@csrf_exempt
def enregistrer_resultat_match(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            gagnant_id = data.get("winner")
            score_joueur1 = int(data.get("player1_score", 0))
            score_joueur2 = int(data.get("player2_score", 0))
            if not gagnant_id:
                return JsonResponse({"status": "error", "message": "Gagnant non défini"}, status=400)
            # Récupérer le gagnant
            gagnant = get_object_or_404(match.tournoi.joueurs.model, id=gagnant_id)
            # Récupérer le nom personnalisé du gagnant
            gagnant_nom_personnalise = match.tournoi.joueurs_noms_personnalises.get(str(gagnant.id), gagnant.nom)
            # Mettre à jour le match
            match.gagnant = gagnant
            match.gagnant_nom = gagnant_nom_personnalise  # Enregistrer le nom personnalisé
            match.score_joueur1 = score_joueur1
            match.score_joueur2 = score_joueur2
            match.save()
            # Mettre à jour le tournoi après l'enregistrement du match
            match.tournoi.mettre_a_jour_tournoi()

            return JsonResponse({"status": "success", "message": f"Résultat enregistré pour {gagnant_nom_personnalise}"})
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Format JSON invalide"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Requête invalide"}, status=400)


@login_required
def jeu_tournois(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    tournoi = match.tournoi

    context = {
        "match": match,
        "joueur1_nom": match.joueur1_nom,
        "joueur2_nom": match.joueur2_nom,
        "tournoi_id": tournoi.id,
        "match_id": match_id
    }
    return render(request, "tournois/jeu_tournois.html", context)

@csrf_exempt
def save_game_result(request):
    if request.method == 'POST':
        match_id = request.POST.get('match_id')
        player1_score = int(request.POST.get('player1_score', 0))
        player2_score = int(request.POST.get('player2_score', 0))
        winner_id = request.POST.get('winner')

        match = get_object_or_404(Match, id=match_id)

        # Mise à jour des scores et du gagnant
        match.score_joueur1 = player1_score
        match.score_joueur2 = player2_score

        if winner_id == str(match.joueur1.id):
            match.gagnant = match.joueur1
        elif winner_id == str(match.joueur2.id):
            match.gagnant = match.joueur2
        else:
            return JsonResponse({'status': 'error', 'message': 'ID du gagnant invalide'})

        match.save()

        # Mise à jour du tournoi
        match.tournoi.mettre_a_jour_tournoi()

        return JsonResponse({'status': 'success', 'message': 'Résultat enregistré'})
    return JsonResponse({'status': 'error', 'message': 'Requête invalide'})



@login_required
def detail_tournoi(request, tournoi_id):
    tournoi = get_object_or_404(Tournoi, id=tournoi_id)
    joueurs = list(tournoi.joueurs.all())
    matches = list(tournoi.matchs.all().order_by('ordre'))

    # Récupère les noms personnalisés ou les noms par défaut
    joueurs_affichage = [
        tournoi.joueurs_noms_personnalises.get(str(joueur.id), joueur.nom)
        for joueur in joueurs
    ]

    # Récupère le nom personnalisé de l'utilisateur connecté
    nom_utilisateur_tournoi = tournoi.joueurs_noms_personnalises.get(str(request.user.id), request.user.nom)

    context = {
        'tournoi': tournoi,
        'joueur1': joueurs_affichage[0] if len(joueurs_affichage) > 0 else None,
        'joueur2': joueurs_affichage[1] if len(joueurs_affichage) > 1 else None,
        'joueur3': joueurs_affichage[2] if len(joueurs_affichage) > 2 else None,
        'joueur4': joueurs_affichage[3] if len(joueurs_affichage) > 3 else None,
        'matches': matches,
        'joueurs': joueurs_affichage,  # Liste des noms personnalisés des joueurs
        'nom_utilisateur_tournoi': nom_utilisateur_tournoi,  # Nom personnalisé de l'utilisateur connecté
    }
    return render(request, 'tournois/detail_tournois.html', context)

@login_required
def historique_tournoi(request, tournoi_id):
    tournoi = get_object_or_404(Tournoi, id=tournoi_id)
    matchs = tournoi.matchs.all().order_by("date_match")
    return render(request, "tournois/historique_tournoi.html", {"tournoi": tournoi, "matchs": matchs})


@login_required
def classement_tournoi(request, tournoi_id):
    tournoi = get_object_or_404(Tournoi, id=tournoi_id)
    classement = Classement.objects.filter(tournoi=tournoi).order_by("-points")
    return render(request, "tournois/classement_tournoi.html", {"tournoi": tournoi, "classement": classement})

def mettre_a_jour_tournoi(self):
    """Met à jour la finale avec les gagnants des demi-finales."""
    matchs = list(self.matchs.all().order_by("round"))

    if len(matchs) == 3 and all(m.gagnant for m in matchs[:2]):  # Si les deux demi-finales ont un gagnant
        finale = matchs[2]
        finale.joueur1 = matchs[0].gagnant
        finale.joueur2 = matchs[1].gagnant
        finale.save()

    if len(matchs) == 3 and matchs[2].gagnant:  # Si la finale a un gagnant
        self.gagnant_final = matchs[2].gagnant
        self.statut = "termine"
        self.save()


@login_required
def get_joueurs_noms(request, tournoi_id):
    tournoi = get_object_or_404(Tournoi, id=tournoi_id)
    joueurs = tournoi.joueurs.all()
    # Construire une liste avec les noms personnalisés ou les noms par défaut
    joueurs_data = [
        {
            "id": joueur.id,
            "nom": tournoi.joueurs_noms_personnalises.get(str(joueur.id), joueur.nom)
        }
        for joueur in joueurs
    ]
    return JsonResponse({"joueurs": joueurs_data})


@login_required
def get_tournament_status(request, tournoi_id):
    tournoi = get_object_or_404(Tournoi, id=tournoi_id)
    return JsonResponse({
        'statut': tournoi.statut,
        'is_creator': request.user == tournoi.createur,
        'creator_name': tournoi.joueurs_noms_personnalises.get(str(tournoi.createur.id), tournoi.createur.nom),
        'players_count': tournoi.joueurs.count()
    })
    

@login_required
def get_tournoi_info(request, tournoi_id):
    tournoi = get_object_or_404(Tournoi, id=tournoi_id)
    data = {
        "statut": tournoi.get_statut_display(),
        "joueurs_count": tournoi.joueurs.count(),
    }
    return JsonResponse(data)

@login_required
def get_tournoi_ready_status(request, tournoi_id):
    tournoi = get_object_or_404(Tournoi, id=tournoi_id)
    data = {
        "is_ready": tournoi.joueurs.count() == 4 and tournoi.statut == "en_attente",
        "is_creator": request.user == tournoi.createur,
    }
    return JsonResponse(data)