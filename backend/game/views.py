from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Game, MorpionMatch
from tournois.models import Tournoi
import json
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages 
from django.db import transaction
from django.contrib.auth import get_user_model
import logging
from auth_app.models import Utilisateurs  # Import du modèle utilisateur personnalisé
from django.db.models import Q
from django.utils import timezone

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
            # Récupérer les données POST
            winner = request.POST.get('winner')
            player1_score = int(request.POST.get('player1_score', 0))
            player2_score = int(request.POST.get('player2_score', 0))
            invited_by = request.session.get('invited_by')
            if invited_by:
                player2_name = invited_by
            else:
                player2_name = request.POST.get('player2', 'Player 2')
            
            print(f"Sauvegarde de partie: {request.user.nom} vs {player2_name}, Score: {player1_score}-{player2_score}, Winner: {winner}")
            
            # Supprimer toutes les parties "En cours" obsolètes pour ce joueur
            old_games = Game.objects.filter(
                player1=request.user,
                winner="En cours",
                player1_score=0,
                player2_score=0
            )
            deleted_count = old_games.count()
            old_games.delete()
            print(f"Nettoyage: {deleted_count} parties 'En cours' supprimées")
            # Une seule entrée pour le joueur actuel
            game, created = Game.objects.update_or_create(
                player1=request.user,
                player2=player2_name,
                winner="En cours",  # Condition pour trouver une partie existante
                defaults={
                    'player1_score': player1_score,
                    'player2_score': player2_score,
                    'winner': winner,
                    'name': "Pong Match"
                }
            )
            if created:
                print(f"Nouvelle partie créée: ID={game.id}")
            else:
                print(f"Partie existante mise à jour: ID={game.id}")
            # Désactiver l'état "en train de jouer" pour le joueur actuel
            request.user.is_playing = False
            request.user.save(update_fields=['is_playing'])
            # 3. PARTIE MIROIR: Créer/mettre à jour une entrée pour l'adversaire si c'était une invitation
            if invited_by:
                try:
                    player2_user = Utilisateurs.objects.get(nom=invited_by)
                    # Supprimer aussi les parties "En cours" obsolètes pour l'adversaire
                    old_mirror_games = Game.objects.filter(
                        player1=player2_user,
                        winner="En cours",
                        player1_score=0,
                        player2_score=0
                    )
                    deleted_mirror_count = old_mirror_games.count()
                    old_mirror_games.delete()
                    print(f"Nettoyage miroir: {deleted_mirror_count} parties 'En cours' supprimées pour {player2_user.nom}")
                    # Créer/mettre à jour l'entrée miroir pour l'adversaire
                    mirror_game, mirror_created = Game.objects.update_or_create(
                        player1=player2_user,
                        player2=request.user.nom,
                        winner="En cours",  # Condition pour trouver une partie existante
                        defaults={
                            'player1_score': player2_score,
                            'player2_score': player1_score,
                            'winner': winner,
                            'name': "Pong Game (via invitation)"
                        }
                    )
                    if mirror_created:
                        print(f"Nouvelle partie miroir créée: ID={mirror_game.id}")
                    else:
                        print(f"Partie miroir mise à jour: ID={mirror_game.id}")
                    # Désactiver l'état "en train de jouer" pour l'adversaire
                    player2_user.is_playing = False
                    player2_user.save(update_fields=['is_playing'])
                    
                    # Nettoyer la session
                    if 'invited_by' in request.session:
                        del request.session['invited_by']
                except Utilisateurs.DoesNotExist:
                    print(f"Utilisateur {invited_by} non trouvé")
                except Exception as e:
                    print(f"Erreur lors de la gestion de l'entrée miroir: {str(e)}")
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Erreur dans save_game_result: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})



@login_required
def dashboard(request):
    user = request.user
    
    # NETTOYAGE: Supprimer les parties 0-0 "En cours" qui traînent
    Game.objects.filter(
        player1=user,
        player1_score=0,
        player2_score=0,
        winner="En cours"
    ).delete()
    
    # Récupérer uniquement les parties terminées
    all_games = Game.objects.filter(
        Q(player1=user) | Q(player2=user.nom)
    ).exclude(
        winner="En cours"
    ).order_by('-created_at')
    
    # Création d'une liste sans doublons avec normalisation des participants
    unique_games = []
    seen_matches = set()
    
    for game in all_games:
        # Normaliser les noms de joueurs (convertir player1 en chaîne si c'est un objet)
        player1_name = game.player1.nom if hasattr(game.player1, 'nom') else str(game.player1)
        player2_name = str(game.player2)
        
        # Normaliser la signature en triant les joueurs alphabétiquement
        players = sorted([player1_name, player2_name])
        
        # Trier les scores selon l'ordre des joueurs normalisés
        if players[0] == player1_name:
            scores = [game.player1_score, game.player2_score]
        else:
            scores = [game.player2_score, game.player1_score]
        
        # Créer une signature qui identifie le match indépendamment de qui est player1/player2
        match_signature = f"{game.created_at.strftime('%Y%m%d%H%M')}_{players[0]}_{players[1]}_{scores[0]}_{scores[1]}"
        
        if match_signature not in seen_matches:
            # Privilégier les parties où l'utilisateur actuel est player1
            if player1_name == user.nom:
                unique_games.append(game)
            else:
                # Ajouter la partie sans vérification supplémentaire (simplification)
                unique_games.append(game)
                    
            seen_matches.add(match_signature)
    
    # Utiliser uniquement les parties uniques
    games = unique_games[:10]  # Limiter à 10 parties
    
    # Calculer les statistiques (ajuster pour utiliser player1_name)
    games_won = 0
    games_lost = 0
    
    for g in unique_games:
        p1_name = g.player1.nom if hasattr(g.player1, 'nom') else str(g.player1)
        p2_name = str(g.player2)
        
        if (p1_name == user.nom and g.player1_score > g.player2_score) or (p2_name == user.nom and g.player2_score > g.player1_score):
            games_won += 1
        elif (p1_name == user.nom and g.player1_score < g.player2_score) or (p2_name == user.nom and g.player2_score < g.player1_score):
            games_lost += 1
    
    total_games = len(unique_games)
    
    # Récupérer les matches de Morpion
    morpion_matches = MorpionMatch.objects.all().order_by("-created_at")
    
    # Calculer la progression et le niveau
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

    print(f"Parties uniques trouvées: {total_games} (affichées: {len(games)})")
    print(f"Statistiques: {games_won} victoires, {games_lost} défaites")
    
    context = {
        "user": user,
        "games": games,
        "total_score": total_score,
        "games_won": games_won,
        "games_lost": games_lost,
        "level_progress": level_progress,
        "level": level,
        "tournois": Tournoi.objects.all(),
        "morpion_matches": morpion_matches,  # Ajout des matches de Morpion au contexte
        "total_games": total_games,
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

@login_required
def join_game(request):
    game_type = request.GET.get('game')
    creator = request.GET.get('creator')
    
    # Récupérer l'utilisateur créateur
    creator_user = get_object_or_404(Utilisateurs, nom=creator)
    
    if game_type == 'morpion':
        # Logique pour le Morpion (inchangée)
        match, created = MorpionMatch.objects.get_or_create(
            creator=creator_user,
            status='waiting'
        )
        
        match.players.add(request.user)
        
        if match.is_full():
            match.status = 'in_progress'
            match.save()
            
        return redirect('morpion_match_detail', match_id=match.id)
    
    elif game_type == 'pong':
        try:
            # Marquer l'utilisateur qui rejoint comme étant en train de jouer
            request.user.is_playing = True
            request.user.save(update_fields=['is_playing'])
            
            # Marquer également le créateur comme étant en train de jouer
            creator_user.is_playing = True
            creator_user.save(update_fields=['is_playing'])
            
            # Chercher si une partie existe déjà avec ce créateur
            existing_game = Game.objects.filter(
                player1=creator_user,
                winner="En cours"
            ).first()
            
            if existing_game:
                # Si une partie existe, la rejoindre
                existing_game.player2 = request.user.nom
                existing_game.save()
                
                # Stockage de l'information sur qui est le créateur dans la session
                request.session['invited_by'] = creator
                
                return redirect('start_game')
            else:
                # Créer une nouvelle partie explicitement pour cette invitation
                with transaction.atomic():
                    # Créer la partie avec ce joueur comme player1 et le créateur comme player2
                    game = Game.objects.create(
                        player1=request.user,
                        player2=creator_user.nom,  # Nom de l'expéditeur comme player2
                        player1_score=0,
                        player2_score=0,
                        winner="En cours"
                    )
                    
                    # Stockage de l'information sur qui est le créateur dans la session
                    request.session['invited_by'] = creator
                    
                    print(f"Partie créée - ID: {game.id}, Joueur2: {creator_user.nom}")
                    
                    return redirect('start_game')
                    
        except Exception as e:
            print(f"Erreur lors de la redirection vers Pong: {str(e)}")
            return redirect('start_game')
    
    return redirect('dashboard')

@login_required
def invited_game(request):
    inviter_name = request.GET.get('from')
    if not inviter_name:
        return redirect('dashboard')
        
    inviter = get_object_or_404(Utilisateurs, nom=inviter_name)
    
    # Stockez l'inviteur dans la session pour une utilisation ultérieure
    request.session['invited_by'] = inviter_name
    
    context = {
        'inviter': inviter,
        'is_invited_game': True,
        'user': request.user
    }
    
    return render(request, "game/invited_game.html", context)


@login_required
def get_morpion_matches(request):
    try:
        matches = MorpionMatch.objects.all().order_by('-created_at')
        data = {
            'matches': [{
                'id': match.id,
                'creator_name': match.creator.nom,
                'status': match.get_status_display(),
                'player_count': match.players.count(),
                'is_full': match.players.count() >= 2,
                'has_joined': request.user in match.players.all()
            } for match in matches]
        }
        return JsonResponse(data)
    except Exception as e:
        print(f"Error in get_morpion_matches: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_tournaments(request):
    tournaments = Tournoi.objects.all()
    data = {
        'tournaments': [{
            'id': tournament.id,
            'creator_name': tournament.createur.nom,
            'status': tournament.get_statut_display(),
            'player_count': tournament.joueurs.count(),
            'is_full': tournament.est_complet(),
            'has_joined': request.user in tournament.joueurs.all()
        } for tournament in tournaments]
    }
    return JsonResponse(data)