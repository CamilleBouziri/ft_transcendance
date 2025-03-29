from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from random import shuffle
from .models import Tournoi, Match, Classement
from django.views.decorators.csrf import csrf_exempt


@login_required
def creer_tournoi(request):
    if request.method == "POST":
        nom = request.POST.get("nom")
        if not nom:
            messages.error(request, "Le nom du tournoi est obligatoire.")
            return redirect("creer_tournois")
        tournoi = Tournoi.objects.create(nom=nom, createur=request.user)
        tournoi.joueurs.add(request.user)
        messages.success(request, "Tournoi créé avec succès.")
        return redirect("dashboard")
    return render(request, "tournois/creer_tournois.html")

@login_required
def rejoindre_tournoi(request, tournoi_id):
    tournoi = get_object_or_404(Tournoi, id=tournoi_id)
    if tournoi.est_complet():
        messages.error(request, "Ce tournoi est déjà complet.")
        return redirect("dashboard")
    if request.user in tournoi.joueurs.all():
        messages.error(request, "Vous êtes déjà inscrit à ce tournoi.")
        return redirect("dashboard")
    tournoi.joueurs.add(request.user)
    messages.success(request, "Vous avez rejoint le tournoi avec succès.")
    return redirect("dashboard")


@login_required
def lancer_tournoi(request, tournoi_id):
    tournoi = get_object_or_404(Tournoi, id=tournoi_id)

    # Vérifie qu'il y a bien 4 joueurs inscrits
    if tournoi.joueurs.count() != 4:
        messages.error(request, "Le tournoi doit avoir 4 joueurs pour être lancé.")
        return redirect('details_tournois', tournoi_id=tournoi.id)

    # Récupère les joueurs
    joueurs = list(tournoi.joueurs.all())  # Convertit QuerySet en liste pour indexation

    # Vérification supplémentaire
    if len(joueurs) < 4:
        messages.error(request, "Problème : pas assez de joueurs pour démarrer le tournoi.")
        return redirect('details_tournois', tournoi_id=tournoi.id)

    # Création des premiers matchs (Demi-finales)
    match1 = Match.objects.create(
        tournoi=tournoi,
        joueur1=joueurs[0],
        joueur2=joueurs[1],
        round="demi_finale"  # Utilisation du bon champ
    )
    
    match2 = Match.objects.create(
        tournoi=tournoi,
        joueur1=joueurs[2],
        joueur2=joueurs[3],
        round="demi_finale"  # Utilisation du bon champ
    )

    # Marque le tournoi comme en cours
    tournoi.statut = "en_cours"
    tournoi.save()

    messages.success(request, "Le tournoi a été lancé avec succès !")
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

            gagnant = get_object_or_404(match.tournoi.joueurs.model, id=gagnant_id)
            match.gagnant = gagnant
            match.score_joueur1 = score_joueur1
            match.score_joueur2 = score_joueur2
            match.save()

            # 🔥 Mettre à jour le tournoi après l'enregistrement du match
            match.tournoi.mettre_a_jour_tournoi()

            return JsonResponse({"status": "success", "message": "Résultat enregistré"})

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
        "joueur1_nom": match.joueur1.nom if match.joueur1 else "Joueur 1",
        "joueur2_nom": match.joueur2.nom if match.joueur2 else "Joueur 2",
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
    joueurs = list(tournoi.joueurs.all().order_by("id"))
    matchs = list(tournoi.matchs.all().order_by("round", "date_match"))  # 🔥 Assure-toi que ça récupère bien les matchs !

    return render(request, "tournois/detail_tournois.html", {
        "tournoi": tournoi,
        "joueur1": joueurs[0] if len(joueurs) > 0 else None,
        "joueur2": joueurs[1] if len(joueurs) > 1 else None,
        "joueur3": joueurs[2] if len(joueurs) > 2 else None,
        "joueur4": joueurs[3] if len(joueurs) > 3 else None,
        "matches": matchs,  # 🔥 Vérifie que tu passes bien "matches" au template
    })


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


