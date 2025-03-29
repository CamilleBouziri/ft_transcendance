from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateurs

class CustomUserCreationForm(UserCreationForm):
    nom = forms.CharField(
        label="Nom d'utilisateur",
        max_length=50,
        widget=forms.TextInput(attrs={'autocomplete': 'username'})
    )
    email = forms.EmailField(
        required=True,
        label="Adresse email",
        widget=forms.EmailInput(attrs={'autocomplete': 'email'})
    )
    password1 = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
    )
    password2 = forms.CharField(
        label="Confirmation du mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
    )

    class Meta:
        model = Utilisateurs
        fields = ('nom', 'email', 'password1', 'password2')

    def clean_nom(self):
        nom = self.cleaned_data.get('nom')
        if Utilisateurs.objects.filter(nom=nom).exists():
            raise forms.ValidationError("Ce nom d'utilisateur existe déjà")
        return nom

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Utilisateurs.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse email existe déjà")
        return email