from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from auth_app import views as auth_views
from game import views as game_views
from tournois import views as tournois_views
from django.conf.urls.i18n import set_language
from django.views.generic import RedirectView  # Importe RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('accounts/', include('allauth.urls')),
    path('home/', include('allauth.urls')),
    path('admin/', admin.site.urls),
    path('auth/', include('auth_app.urls')),
    path('inscription', auth_views.inscription, name='inscription'),
    path('login/', auth_views.connexion, name='login'),
    path('accueil/', auth_views.accueil, name='accueil'),
    path('dashboard/', game_views.dashboard, name='dashboard'),
     path('invited-game/', game_views.invited_game, name='invited_game'),
    path('game/', game_views.start_game, name='start_game'), 
    path('game/join/', game_views.join_game, name='join_game'),

    path('morpion/create/', game_views.create_morpion_match, name='create_morpion_match'),
    path('morpion/join/<int:match_id>/', game_views.join_morpion_match, name='join_morpion_match'),
    path('morpion/match/<int:match_id>/', game_views.morpion_match_detail, name='morpion_match_detail'),
    path('morpion/match/<int:match_id>/status/', game_views.check_match_status, name='check_match_status'),
    path('get-tournaments/', game_views.get_tournaments, name='get_tournaments'),
    path('get-morpion-matches/', game_views.get_morpion_matches, name='get_morpion_matches'),

    path("create_tournois/", tournois_views.creer_tournoi, name="creer_tournois"),
    path("join_tournament/<int:tournoi_id>/", tournois_views.rejoindre_tournoi, name="rejoindre_tournoi"),
    path("lancer_tournois/<int:tournoi_id>/", tournois_views.lancer_tournoi, name="lancer_tournois"),
    path("details_tournois/<int:tournoi_id>/", tournois_views.detail_tournoi, name="details_tournois"),
    path("tournoi/<int:tournoi_id>/historique/", tournois_views.historique_tournoi, name="historique_tournoi"),
    path("tournoi/<int:tournoi_id>/classement/", tournois_views.classement_tournoi, name="classement_tournoi"),
    path("enregistrer_resultat_match/<int:match_id>/", tournois_views.enregistrer_resultat_match, name="enregistrer_resultat_match"),
    path("rejoindre_tournoi/<int:tournoi_id>/", tournois_views.rejoindre_tournoi, name="rejoindre_tournois"),
    path('tournois/<int:tournoi_id>/info/', tournois_views.get_tournoi_info, name='get_tournoi_info'),
    path('tournois/<int:tournoi_id>/ready-status/', tournois_views.get_tournoi_ready_status, name='get_tournoi_ready_status'),

    path('tournois/<int:tournoi_id>/status/', tournois_views.get_tournament_status, name='get_tournament_status'),
    path('get_joueurs_noms/<int:tournoi_id>/', tournois_views.get_joueurs_noms, name='get_joueurs_noms'),
    path("jeu_tournois/<int:match_id>/", tournois_views.jeu_tournois, name="jeu_tournois"),
    path('', include('social_django.urls', namespace='social')),
    path('save-result/', game_views.save_game_result, name='save_game_result'),
    path('start-game/', game_views.start_game, name='start-game'),
    path('', RedirectView.as_view(url='auth/connexion/', permanent=True), name='connexion_redirect'),
    path('set_language/', set_language, name='set_language'),

    path("morpion/", game_views.morpion, name="morpion"),
    path("save-morpion-result/", game_views.save_morpion_result, name="save_morpion_result"),


    path('amis/', include('amis.urls')),
    path('chat/', include('chat.urls', namespace='chat')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)