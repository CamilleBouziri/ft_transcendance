from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('api/block-user/', views.block_user, name='block_user'),
    path('', views.index, name='index'),
    path('create/', views.create_room, name='create_room'),
    path('conversations/', views.conversations_list, name='conversations_list'),
    path('<str:room_name>/', views.room, name='room'),
] 