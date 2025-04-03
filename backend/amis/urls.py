from django.urls import path
from .views import rechercher_utilisateur, envoyer_demande_ami, amis, accepter_demande_ami, refuser_demande_ami, supprimer_ami, get_friends_status, get_friend_requests, get_pending, get_friends, profil_ami

urlpatterns = [
    path('rechercher/', rechercher_utilisateur, name='rechercher_utilisateur'),
    path('ajouter/<int:utilisateur_id>/', envoyer_demande_ami, name='envoyer_demande_ami'),
	path('amis/', amis, name='amis'),
    path('accepter-demande/<int:demande_id>/', accepter_demande_ami, name='accepter_demande_ami'),
    path('refuser-demande/<int:demande_id>/', refuser_demande_ami, name='refuser_demande_ami'),
    path('supprimer-ami/<int:ami_id>/', supprimer_ami, name='supprimer_ami'),
    path('get-status/', get_friends_status, name='get_friends_status'),
    path('get-requests/', get_friend_requests, name='get_friend_requests'),
    path('get-pending/', get_pending, name='get_pending'),
    path('get-friends/', get_friends, name='get_friends'),
    path('profil/<str:ami_nom>/', profil_ami, name='profil_ami'),
]