from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from auth_app.models import Utilisateurs
from .models import Ami
from django.db import models
from django.http import JsonResponse

@login_required
def rechercher_utilisateur(request):
    query = request.GET.get('q', '').strip()
    utilisateurs = []

    if query:
        utilisateurs = Utilisateurs.objects.filter(nom__icontains=query).exclude(nom=request.user.nom)
        amis = Ami.objects.filter(utilisateur=request.user).values_list('ami', flat=True)
        demandes_recues = Ami.objects.filter(ami=request.user).values_list('utilisateur', flat=True)
        utilisateurs = utilisateurs.exclude(id__in=amis).exclude(id__in=demandes_recues)

    return redirect('amis')

@login_required
def envoyer_demande_ami(request, utilisateur_id):
    utilisateur_cible = get_object_or_404(Utilisateurs, id=utilisateur_id)

    if Ami.objects.filter(utilisateur=request.user, ami=utilisateur_cible).exists():
        return redirect('rechercher_utilisateur')

    Ami.objects.create(utilisateur=request.user, ami=utilisateur_cible, statut='en_attente')

    return redirect('rechercher_utilisateur')
    

@login_required
def amis(request):
    query = request.GET.get('q', '').strip()
    utilisateurs = []

    if query:
        utilisateurs = Utilisateurs.objects.filter(nom__icontains=query).exclude(nom=request.user.nom)
        
        amis_exclus = Ami.objects.filter(
            models.Q(utilisateur=request.user, statut__in=['accepte', 'en_attente']) |
            models.Q(ami=request.user, statut__in=['accepte', 'en_attente'])
        ).values_list('ami', 'utilisateur')
        
        ids_a_exclure = set()
        for ami_id, utilisateur_id in amis_exclus:
            if ami_id != request.user.id:
                ids_a_exclure.add(ami_id)
            if utilisateur_id != request.user.id:
                ids_a_exclure.add(utilisateur_id)
        
        utilisateurs = utilisateurs.exclude(id__in=ids_a_exclure)
    
    demandes_envoyees = Ami.objects.filter(utilisateur=request.user, statut='en_attente')
    demandes_recues = Ami.objects.filter(ami=request.user, statut='en_attente')
    amis_acceptes_envoyees = Ami.objects.filter(utilisateur=request.user, statut='accepte')
    amis_acceptes_recues = Ami.objects.filter(ami=request.user, statut='accepte')
    
    amis_acceptes = {
        'envoyes': amis_acceptes_envoyees,
        'recus': amis_acceptes_recues
    }

    return render(request, 'amis/amis.html', {
        'utilisateurs': utilisateurs,
        'query': query,
        'demandes_envoyees': demandes_envoyees,
        'demandes_recues': demandes_recues,
        'amis_acceptes': amis_acceptes
    })

@login_required
def accepter_demande_ami(request, demande_id):
    demande = get_object_or_404(Ami, id=demande_id, ami=request.user, statut='en_attente')
    demande.statut = 'accepte'
    demande.save()
    return redirect('amis')

@login_required
def refuser_demande_ami(request, demande_id):
    demande = get_object_or_404(Ami, id=demande_id, ami=request.user, statut='en_attente')
    demande.statut = 'refuse'
    demande.save()
    return redirect('amis')
    
@login_required
def supprimer_ami(request, ami_id):
    ami = get_object_or_404(
        Ami, 
        (models.Q(utilisateur=request.user, ami_id=ami_id) | 
         models.Q(ami=request.user, utilisateur_id=ami_id)),
        statut='accepte'
    )
    ami.delete()
    return redirect('amis')
# 

@login_required
def get_friends_status(request):
    amis_envoyes = Ami.objects.filter(utilisateur=request.user, statut='accepte')
    amis_recus = Ami.objects.filter(ami=request.user, statut='accepte')
    
    friends_status = []
    
    # Changement de 'Ami' en 'ami' dans la variable de boucle
    for ami in amis_envoyes:
        friends_status.append({
            'id': ami.ami.id,
            'is_online': ami.ami.is_online,
            'is_playing': ami.ami.is_playing
        })
    
    # Changement de 'Ami' en 'ami' dans la variable de boucle
    for ami in amis_recus:
        friends_status.append({
            'id': ami.utilisateur.id,
            'is_online': ami.utilisateur.is_online,
            'is_playing': ami.utilisateur.is_playing
        })
    
    return JsonResponse({'friends': friends_status})

@login_required
def get_friend_requests(request):
    demandes_recues = Ami.objects.filter(ami=request.user, statut='en_attente')
    
    requests_data = {
        'received_requests': [
            {
                'id': demande.id,
                'utilisateur': {
                    'id': demande.utilisateur.id,
                    'nom': demande.utilisateur.nom
                }
            } for demande in demandes_recues
        ]
    }
    
    return JsonResponse(requests_data)

@login_required
def get_pending(request):
    demandes_envoyees = Ami.objects.filter(
        utilisateur=request.user,
        statut='en_attente'
    )
    
    pending_requests = [{
        'id': demande.id,
        'ami': {
            'id': demande.ami.id,
            'nom': demande.ami.nom
        }
    } for demande in demandes_envoyees]
    
    return JsonResponse({'pending_requests': pending_requests})

@login_required
def get_friends(request):
    amis_envoyes = Ami.objects.filter(utilisateur=request.user, statut='accepte')
    amis_recus = Ami.objects.filter(ami=request.user, statut='accepte')
    
    friends = []
    
    for ami in amis_envoyes:
        friends.append({
            'id': ami.ami.id,
            'nom': ami.ami.nom,
            'is_online': ami.ami.is_online,
            'is_playing': ami.ami.is_playing
        })
    
    for ami in amis_recus:
        friends.append({
            'id': ami.utilisateur.id,
            'nom': ami.utilisateur.nom,
            'is_online': ami.utilisateur.is_online,
            'is_playing': ami.utilisateur.is_playing
        })
    
    return JsonResponse({'friends': friends})

@login_required
def profil_ami(request, ami_nom):
    ami = get_object_or_404(Utilisateurs, nom=ami_nom)
    
    # Vérifier si l'utilisateur est ami avec la personne
    est_ami = Ami.objects.filter(
        (models.Q(utilisateur=request.user, ami=ami) |
         models.Q(utilisateur=ami, ami=request.user)),
        statut='accepte'
    ).exists()
    
    if not est_ami:
        return redirect('amis')
        
    return render(request, 'amis/profil_ami.html', {
        'ami': ami,
    })