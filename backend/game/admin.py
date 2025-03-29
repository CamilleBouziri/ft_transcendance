from django.contrib import admin
from .models import Game

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'player1', 'player2', 'player1_score', 'player2_score', 'winner', 'created_at')
    list_filter = ('winner', 'created_at')
    search_fields = ('player1__nom', 'player2')
