from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Game
from tournois.models import Tournoi
import json
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from django.db import transaction
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

@login_required
@csrf_exempt  # Ajout du décorateur pour éviter les problèmes CSRF
def start_game(request):
    print("Début de start_game")
    
    if request.method == "POST":
        try:
            data = json.loads(request.body) if request.body else {}
            
            with transaction.atomic():
                # Récupérer une version fraîche de l'utilisateur
                User = get_user_model()
                player1 = User.objects.select_for_update().get(pk=request.user.pk)
                
                # Mettre à jour le statut avec update_fields
                player1.is_playing = True
                player1.save(update_fields=['is_playing'])
                
                # Créer la partie avec les scores initiaux
                game = Game.objects.create(
                    player1=player1,
                    player1_score=data.get('player1_score', 0),
                    player2_score=data.get('player2_score', 0),
                    winner="En cours"
                )
                
                print(f"Partie créée - ID: {game.id}, is_playing: {player1.is_playing}")
                
                return JsonResponse({
                    "status": "success",
                    "game_id": game.id,
                    "is_playing": player1.is_playing
                })
                
        except Exception as e:
            print(f"ERREUR dans start_game: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)})

    return render(request, "game/index.html")

# @login_required
# def start_game(request):
#     print("Début de start_game")  # Debug print
#     if request.method == "POST":
#         try:
#             with transaction.atomic():
#                 print(f"POST reçu pour l'utilisateur {request.user.nom}")  # Debug print
                
#                 # Récupérer une version fraîche de l'utilisateur
#                 User = get_user_model()
#                 player1 = User.objects.select_for_update().get(pk=request.user.pk)
#                 print(f"Utilisateur récupéré: {player1.nom}")  # Debug print
                
#                 # Mettre à jour le statut
#                 player1.is_playing = True
#                 player1.save()
#                 print(f"Statut mis à jour: is_playing = {player1.is_playing}")  # Debug print
                
#                 # Vérifier la mise à jour
#                 player1.refresh_from_db()
#                 print(f"Après refresh: is_playing = {player1.is_playing}")  # Debug print
                
#                 # Créer la partie
#                 player1_score = int(request.POST.get("player1_score", 0))
#                 player2_score = int(request.POST.get("player2_score", 0))
#                 winner = player1.nom if player1_score > player2_score else "Player 2"
                
#                 game = Game.objects.create(
#                     player1=player1,
#                     player1_score=player1_score,
#                     player2_score=player2_score,
#                     winner=winner
#                 )
#                 print(f"Partie créée avec l'ID: {game.id}")  # Debug print
                
#                 return JsonResponse({
#                     "status": "success", 
#                     "game_id": game.id,
#                     "is_playing": player1.is_playing
#                 })
                
#         except Exception as e:
#             print(f"ERREUR: {str(e)}")  # Debug print
#             return JsonResponse({"status": "error", "message": str(e)})

#     return render(request, "game/index.html")

# @login_required
# def start_game(request):

#     if request.method == "POST":
#         player1 = request.user
#         player1_score = int(request.POST.get("player1_score", 0))
#         player2_score = int(request.POST.get("player2_score", 0))
#         winner = player1.nom if player1_score > player2_score else "Player 2"
        
#         # Crée une nouvelle partie
#         game = Game.objects.create(
#             player1=player1,
#             player1_score=player1_score,
#             player2_score=player2_score,
#             winner=winner,
#         )
#         return JsonResponse({"status": "success", "game_id": game.id})

#     return render(request, "game/index.html")


@login_required
@csrf_protect
def save_game_result(request):
    if request.method == 'POST':
        try:
            # # Créer une nouvelle partie
            # game = Game(
            #     player1=request.user,
            #     player2=request.POST.get('player2', 'Player 2'),
            #     winner=request.POST.get('winner'),
            #     player1_score=request.POST.get('player1_score'),
            #     player2_score=request.POST.get('player2_score'),
            # )
            # Récupérer la dernière partie créée par l'utilisateur
            game = Game.objects.filter(
                player1=request.user,
                winner="En cours"
            ).latest('created_at')
            
            # Mettre à jour les données de la partie
            game.player2 = request.POST.get('player2', 'Player 2')
            game.winner = request.POST.get('winner')
            game.player1_score = request.POST.get('player1_score')
            game.player2_score = request.POST.get('player2_score')
            game.save()

            player1 = request.user
            player1.is_playing = False
            player1.save(update_fields=['is_playing'])

            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})



@login_required
def dashboard(request):
    user = request.user

    tournois = Tournoi.objects.all()
    
    # Récupérer toutes les parties (Pong + Morpion)
    games = Game.objects.filter(player1=user).order_by("-created_at")
    total_games = games.count()

    # Calculer les victoires et défaites
    games_won = games.filter(winner=user.nom).count()
    games_lost = total_games - games_won

    # Calcul de la progression et du niveau
    level_progress = (games_won * 20) % 100
    level = games_won // 5

    # Mise à jour des statistiques utilisateur
    if hasattr(user, 'wins') and hasattr(user, 'losses'):
        if user.wins != games_won or user.losses != games_lost:
            user.wins = games_won
            user.losses = games_lost
            user.save()

    # Score total de l'utilisateur
    total_score = sum(game.player1_score for game in games)

    context = {
        "user": user,
        "games": games,
        "total_score": total_score,
        "games_won": games_won,
        "games_lost": games_lost,
        "level_progress": level_progress,
        "level": level,
        "tournois": tournois,
    }

    return render(request, "game/dashboard.html", context)



@login_required
def morpion(request):
    """Affiche le jeu de morpion"""
    return render(request, "game/morpion.html")




@login_required
@csrf_exempt
def save_morpion_result(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            player1_score = int(data.get('player1_score', 0))
            player2_score = int(data.get('player2_score', 0))

            game = Game.objects.create(
                player1=request.user,
                name="Morpion Game",
                player2=data.get('player2', 'Player 2'),
                winner=data.get('winner'),
                player1_score=player1_score,
                player2_score=player2_score
            )

            return JsonResponse({'status': 'success', 'game_id': game.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})