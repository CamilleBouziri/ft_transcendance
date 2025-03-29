from django.contrib import admin
from .models import Tournoi, Match, Classement

class MatchInline(admin.TabularInline):
    model = Match
    extra = 0
    fields = ("joueur1", "joueur2", "gagnant", "score_joueur1", "score_joueur2", "date_match")
    readonly_fields = ("date_match",)

class ClassementInline(admin.TabularInline):
    model = Classement
    extra = 0
    fields = ("joueur", "points")
    readonly_fields = ("points",)

class TournoiAdmin(admin.ModelAdmin):
    list_display = ("nom", "createur", "statut", "nombre_joueurs", "date_creation")
    list_filter = ("statut", "date_creation")
    search_fields = ("nom", "createur__username")
    inlines = [MatchInline, ClassementInline]
    filter_horizontal = ("joueurs",)

    def nombre_joueurs(self, obj):
        return obj.joueurs.count()
    nombre_joueurs.short_description = "Nombre de joueurs"

class MatchAdmin(admin.ModelAdmin):
    list_display = ("tournoi", "joueur1", "joueur2", "gagnant", "score_joueur1", "score_joueur2", "date_match")
    list_filter = ("tournoi", "date_match")
    search_fields = ("joueur1__username", "joueur2__username")

class ClassementAdmin(admin.ModelAdmin):
    list_display = ("tournoi", "joueur", "points")
    list_filter = ("tournoi",)
    search_fields = ("joueur__username",)

admin.site.register(Tournoi, TournoiAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(Classement, ClassementAdmin)
