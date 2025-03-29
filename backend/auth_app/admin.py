from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Utilisateurs

@admin.register(Utilisateurs)
class UtilisateursAdmin(admin.ModelAdmin):
    list_display = ('nom', 'is_active', 'is_staff', 'is_superuser')  # Colonnes affichées dans la liste admin
    search_fields = ('nom',)  # Recherche possible dans le champ nom
    list_filter = ('is_active', 'is_staff', 'is_superuser')  # Filtres disponibles
