from django.apps import AppConfig


# class AccountConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'auth_app'

class Auth_AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_app'

    def ready(self):
        import auth_app.signals  # Enregistre les signaux