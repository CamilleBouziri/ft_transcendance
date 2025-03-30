from .form import CustomUserCreationForm
from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth  import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .form import AvatarUploadForm
from .form import ChangeNameForm
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_protect

def inscription(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Enregistrement de l'utilisateur
            user = form.save()
            user.is_online = True
            user = form.save()
            # Connexion automatique après inscription
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('dashboard')  # Redirige vers la page d'accueil ou une autre page
    else:
        form = CustomUserCreationForm()

    return render(request, 'inscription.html', {'form': form})



from django.contrib import messages

def connexion(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            user.is_online = True
            user.save()
            return redirect('dashboard')
        else:
            # Si les identifiants sont invalides, on crée un message d'erreur
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    return render(request, 'connexion.html')



@login_required(login_url='/connexion/', redirect_field_name='suivant')
def accueil(request):
       return render(request, 'accueil.html')

@login_required
def upload_avatar(request):
    if request.method == 'POST':
        form = AvatarUploadForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('dashboard')  # Redirige vers le tableau de bord
    else:
        form = AvatarUploadForm(instance=request.user)
    return render(request, 'upload_avatar.html', {'form': form})

@login_required
def change_name(request):
    if request.method == 'POST':
        form = ChangeNameForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('dashboard')  # Redirige vers le tableau de bord après la modification
    else:
        form = ChangeNameForm(instance=request.user)
    return render(request, 'change_name.html', {'form': form})

import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@login_required
def set_offline(request):
    user = request.user
    logger.info(f"set_offline called for user: {user.nom}")  # Ajoutez ce message de débogage
    user.is_online = False  # Marque l'utilisateur comme hors ligne
    user.save()
    return JsonResponse({'status': 'success'})