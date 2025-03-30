# auth_app/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('connexion/', views.connexion, name='connexion'),
    path('upload-avatar/', views.upload_avatar, name='upload_avatar'),
]