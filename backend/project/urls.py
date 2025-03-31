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
    path('game/', game_views.start_game, name='start_game'), 

    path("create_tournois/", tournois_views.creer_tournoi, name="creer_tournois"),
    path("join_tournament/<int:tournoi_id>/", tournois_views.rejoindre_tournoi, name="rejoindre_tournoi"),
    path("lancer_tournois/<int:tournoi_id>/", tournois_views.lancer_tournoi, name="lancer_tournois"),
    path("details_tournois/<int:tournoi_id>/", tournois_views.detail_tournoi, name="details_tournois"),
    path("tournoi/<int:tournoi_id>/historique/", tournois_views.historique_tournoi, name="historique_tournoi"),
    path("tournoi/<int:tournoi_id>/classement/", tournois_views.classement_tournoi, name="classement_tournoi"),
    path("enregistrer_resultat_match/<int:match_id>/", tournois_views.enregistrer_resultat_match, name="enregistrer_resultat_match"),

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