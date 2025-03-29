from django.contrib import admin
from .models import Room, Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'content', 'timestamp')
    list_filter = ('room', 'user', 'timestamp')
    search_fields = ('content', 'user__username', 'room__name')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    ordering = ('-created_at',)
