from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from auth_app.models import Utilisateurs
from .models import Ami
from django.db import models
from django.http import JsonResponse

"""

    Utilisateur A (utilisateur)         ---( demande d'ami )-->        Utilisateur B (ami)
                                                |
                                    statut = en_attente/accepte/refuse

    Attributs :

    │── utilisateur : ForeignKey → Utilisateurs
    │   └── L'utilisateur qui envoie la demande d'amitié
    │
    │── ami: ForeignKey → Utilisateurs
    │   └── L'utilisateur qui reçoit la demande d'amitié
    │
    │── statut : CharField 
    │   └── Valeurs possibles: 'en_attente', 'accepte', 'refuse'
    │   └── Statut actuel de la demande d'amitié
    │
    │── date_ajout : DateTimeField (auto_now_add=True)
        └── Date et heure de création de la demande d'amitié

"""

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

"""
    ENVOYER UNE DEMANDE D'AMITIÉ

    Utilisateur ─── sélectionne utilisateur_id ──→ Vérification
                                                    │
                                                    V
    Traitements : ┌─── Vérifie si demande déjà existante
                  │     └── Si oui: redirection sans action
                  │
                  └─── Sinon: création d'une demande d'amitié avec statut='en_attente'
                              └── Redirection vers 'rechercher_utilisateur'

    Paramètres :

    │── request : HttpRequest
    │   └── Utilisateur authentifié qui envoie la demande
    │
    │── utilisateur_id : int
    │   └── ID de l'utilisateur à qui envoyer la demande
    │
    └── Return : Redirect vers 'rechercher_utilisateur'

"""

@login_required
def envoyer_demande_ami(request, utilisateur_id):
    utilisateur_cible = get_object_or_404(Utilisateurs, id=utilisateur_id)

    if Ami.objects.filter(utilisateur=request.user, ami=utilisateur_cible).exists():
        return redirect('rechercher_utilisateur')

    Ami.objects.create(utilisateur=request.user, ami=utilisateur_cible, statut='en_attente')

    return redirect('rechercher_utilisateur')

"""

    AFFICHAGE DES AMIS ET DES DEMANDES ENVOYEES ET RECUES

    Utilisateur ─── accède à la page ──→ Système de gestion d'amitié
                                            │
                                            V
    Traitement :  ┌─── Recherche (si query présent)
                  │     └── Filtre utilisateurs correspondants
                  │     └── Exclut utilisateurs déjà liés (amis/demandes)
                  │
                  ├─── Récupère les demandes envoyées (en_attente)
                  │
                  ├─── Récupère les demandes reçues (en_attente)
                  │
                  ├─── Récupère les amis acceptés (envoyés)
                  │
                  └─── Récupère les amis acceptés (reçus)
                                            │
                                            V
                                 Affichage du template 'amis.html'

    Paramètres :
    │── request : HttpRequest
    │   └── Peut contenir 'q': paramètre de recherche dans GET
    │
    └── Return : Rendu du template avec contexte contenant:
        └── utilisateurs: résultats de recherche filtrés
        └── query: terme de recherche utilisé
        └── demandes_envoyees: demandes d'amitié en attente envoyées
        └── demandes_recues: demandes d'amitié en attente reçues
        └── amis_acceptes: dict contenant les relations amicales établies

"""

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

"""
    ACCEPTER UNE DEMANDE D'AMITIÉ
    
    Utilisateur ─── sélectionne demande_id ──→ Vérification
                                                    │
                                                    V
    Traitements : ┌─── Vérifie si demande existe et est en attente
                  │     └── Si oui: met à jour statut à 'accepte'
                  │
                  └─── Redirige vers 'amis'
    
    Paramètres :
    │── request: HttpRequest
    │   └── Utilisateur authentifié qui accepte la demande
    │
    │── demande_id : int
    │   └── ID de la demande à accepter
    │
    └── Return : Redirect vers 'amis'

"""

@login_required
def accepter_demande_ami(request, demande_id):
    demande = get_object_or_404(Ami, id=demande_id, ami=request.user, statut='en_attente')
    demande.statut = 'accepte'
    demande.save()
    return redirect('amis')

"""
    REFUSER UNE DEMANDE D'AMITIÉ

    Utilisateur ─── sélectionne demande_id ──→ Vérification
                                                    │
                                                    V
    Traitements : ┌─── Vérifie si demande existe et est en attente
                  │     └── Si oui: met à jour statut à 'refuse'
                  │
                  └─── Redirige vers 'amis'

    Paramètres :
    │── request: HttpRequest
    │   └── Utilisateur authentifié qui refuse la demande
    │
    │── demande_id: int
    │   └── ID de la demande à refuser
    │
    └── Return: Redirect vers 'amis'

"""

@login_required
def refuser_demande_ami(request, demande_id):
    demande = get_object_or_404(Ami, id=demande_id, ami=request.user, statut='en_attente')
    demande.statut = 'refuse'
    demande.save()
    return redirect('amis')

"""
    SUPPRIMER UN AMI

    Utilisateur ─── sélectionne ami_id ──→ Vérification
                                                    │
                                                    V
    Traitements : ┌─── Vérifie si ami existe et est accepté
                  │     └── Si oui: supprime la relation
                  │
                  └─── Redirige vers 'amis'

    Paramètres :
    │── request: HttpRequest
    │   └── Utilisateur authentifié qui souhaite supprimer l'ami
    │
    │── ami_id: int
    │   └── ID de l'ami à supprimer
    │
    └── Return: Redirect vers 'amis'

"""

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