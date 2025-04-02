from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Game, MorpionMatch
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



@login_required
@csrf_protect
def save_game_result(request):
    if request.method == 'POST':
        try:
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
    
    # Récupérer les matches de Morpion
    morpion_matches = MorpionMatch.objects.all().order_by("-created_at")
    
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
        "morpion_matches": morpion_matches,  # Ajout des matches de Morpion au contexte
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
            match = MorpionMatch.objects.get(id=data.get('match_id'))
            
            # Mettre à jour le statut du match
            match.status = "finished"
            match.player1_score = data.get('player1_score', 0)
            match.player2_score = data.get('player2_score', 0)
            
            # Définir le gagnant
            winner_name = data.get('winner')
            if winner_name == match.creator.nom:
                match.winner = match.creator
            else:
                match.winner = match.players.exclude(id=match.creator.id).first()
            
            match.save()

            # Récupérer le second joueur
            player2 = match.players.exclude(id=match.creator.id).first()

            # Créer une entrée pour le créateur (joueur 1)
            Game.objects.create(
                player1=match.creator,
                player2=player2.nom,
                winner=winner_name,
                player1_score=data.get('player1_score', 0),
                player2_score=data.get('player2_score', 0),
                name="Morpion Game"
            )

            # Créer une entrée pour le second joueur
            Game.objects.create(
                player1=player2,
                player2=match.creator.nom,
                winner=winner_name,
                player1_score=data.get('player2_score', 0),  # Inversé pour le point de vue du joueur 2
                player2_score=data.get('player1_score', 0),  # Inversé pour le point de vue du joueur 2
                name="Morpion Game"
            )

            return JsonResponse({'status': 'success', 'match_id': match.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})




@login_required
def create_morpion_match(request):
    match = MorpionMatch.objects.create(creator=request.user)
    match.players.add(request.user)
    return redirect('morpion_match_detail', match_id=match.id)

@login_required
def join_morpion_match(request, match_id):
    match = get_object_or_404(MorpionMatch, id=match_id)
    
    if not match.is_full():
        match.players.add(request.user)
        if match.can_start():
            match.status = "in_progress"
            match.save()
        return redirect('morpion_match_detail', match_id=match.id)
    
    messages.error(request, "This match is already full.")
    return redirect('dashboard')

@login_required
def morpion_match_detail(request, match_id):
    match = get_object_or_404(MorpionMatch, id=match_id)
    # Vérifie si la partie est en cours
    if match.status == "in_progress":
        # Si l'utilisateur est le créateur, lance la partie
        if request.user == match.creator:
            opponent = match.players.exclude(id=request.user.id).first()
            context = {
                "match": match,
                "opponent": opponent,
                "is_creator": True
            }
            return render(request, "game/morpion.html", context)
        # Si l'utilisateur n'est pas le créateur, redirige vers une page d'information
        else:
            context = {
                "match": match,
                "creator_name": match.creator.nom
            }
            return render(request, "game/not_creator_room.html", context)
    # Si la partie n'est pas encore en cours, affiche la salle d'attente
    return render(request, "game/waiting_room.html", {"match": match})



@login_required
def check_match_status(request, match_id):
    """Vérifie le statut d'un match de Morpion."""
    try:
        match = MorpionMatch.objects.get(id=match_id)
        return JsonResponse({
            'status': match.status,
            'winner': match.winner.nom if match.winner else None,
            'players_count': match.players.count(),
            'is_full': match.is_full()
        })
    except MorpionMatch.DoesNotExist:
        return JsonResponse({'error': 'Match not found'}, status=404)