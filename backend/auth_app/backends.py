from social_core.backends.oauth import BaseOAuth2
from auth_app.models import Utilisateurs
class FortyTwoOAuth2(BaseOAuth2):
    name = '42'
    AUTHORIZATION_URL = 'https://api.intra.42.fr/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://api.intra.42.fr/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    SCOPE_SEPARATOR = ' '
    DEFAULT_SCOPE = ['public']

    def get_user_details(self, response):
        """Return user details from 42 account"""
        return {
            'nom': response.get('login'),
            'email': response.get('email'),
            'photo_url': response.get('image', {}).get('versions', {}).get('medium')
        }
    
    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        url = 'https://api.intra.42.fr/v2/me'
        headers = {'Authorization': f'Bearer {access_token}'}
        return self.get_json(url, headers=headers)

    
def pipeline(backend, user, response, *args, **kwargs):
    if backend.name == '42':
        Utilisateurs.objects.update_or_create(
            nom=user,
            defaults={
                'nom': response.get('login'),
                'email': response.get('email'),
                'photo_url': response.get('image', {}).get('versions', {}).get('medium')
                

                # Ajoutez d'autres champs si nécessaire
            }
        )
        user.is_online = True
        user.save()
