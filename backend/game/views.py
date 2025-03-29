from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Game
from tournois.models import Tournoi
import json
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt


@login_required
def start_game(request):
    if request.method == "POST":
        player1 = request.user
        player1_score = int(request.POST.get("player1_score", 0))
        player2_score = int(request.POST.get("player2_score", 0))
        winner = player1.nom if player1_score > player2_score else "Player 2"

        # Crée une nouvelle partie
        game = Game.objects.create(
            player1=player1,
            player1_score=player1_score,
            player2_score=player2_score,
            winner=winner,
        )
        return JsonResponse({"status": "success", "game_id": game.id})

    return render(request, "game/index.html")


@login_required
@csrf_protect
def save_game_result(request):
    if request.method == 'POST':
        try:
            # Créer une nouvelle partie
            game = Game(
                player1=request.user,
                player2=request.POST.get('player2', 'Player 2'),
                winner=request.POST.get('winner'),
                player1_score=request.POST.get('player1_score'),
                player2_score=request.POST.get('player2_score')
            )
            game.save()
            
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