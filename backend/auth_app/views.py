from .form import CustomUserCreationForm
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth  import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required


def inscription(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Enregistrement de l'utilisateur
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
            return redirect('dashboard')
        else:
            # Si les identifiants sont invalides, on crée un message d'erreur
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    return render(request, 'connexion.html')



@login_required(login_url='/connexion/', redirect_field_name='suivant')
def accueil(request):
       return render(request, 'accueil.html')