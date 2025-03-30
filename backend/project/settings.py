from pathlib import Path
import os 

from django.utils.translation import gettext_lazy as _

from dotenv import load_dotenv
load_dotenv()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "django.contrib.sites",  # new
    "allauth",  # new
    "allauth.account", # gerer creation user mano mano 
	'allauth.socialaccount',
    'allauth.socialaccount.providers.oauth2',
	'auth_app.apps.AccountConfig',
	'social_django',
    'game',
    'tournois',
    'amis',
    'channels',
    'chat',
    'sslserver',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  #pour traduire sites
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
	"allauth.account.middleware.AccountMiddleware",
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
	'social_django.middleware.SocialAuthExceptionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            'debug': DEBUG,
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'
# Configuration Channels
ASGI_APPLICATION = 'project.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", 6379)],  # Le port interne reste 6379
        },
    },
}

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'your_database_name'),
        'USER': os.getenv('POSTGRES_USER', 'your_database_user'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'your_database_password'),
        'HOST': os.getenv('POSTGRES_HOST', 'database'),
        'PORT': '5432',  # Port par défaut pour PostgreSQL
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

SOCIAL_AUTH_42_KEY = os.getenv('SOCIAL_AUTH_42_KEY')
SOCIAL_AUTH_42_SECRET = os.getenv('SOCIAL_AUTH_42_SECRET')
SOCIAL_AUTH_42_SCOPE = ['public']
SOCIAL_AUTH_SKIP_STATE = True

SOCIAL_AUTH_LOGIN_REDIRECT_URL = 'accueil'
SOCIAL_AUTH_LOGIN_ERROR_URL = 'login'

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'auth_app.backends.pipeline',
)


LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_URL = 'logout'
LOGOUT_REDIRECT_URL = 'login'


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('en', _('English')),
    ('fr', _('French')),
    ('es', _('Spanish')),
]

LOCALE_PATHS = [BASE_DIR / 'locale'] 

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'auth_app.Utilisateurs'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'auth_app.backends.FortyTwoOAuth2',
	
]

SITE_ID = 1

SOCIALACCOUNT_ADAPTER = "auth_app.adapters.CustomSocialAccountAdapter"

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'


ACCOUNT_AUTHENTICATION_METHOD = 'username'  # Utilise le champ `nom`
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'nom'  # Spécifie le champ utilisé comme identifiant principal
ACCOUNT_USERNAME_REQUIRED = True  # Le champ `nom` est requis
ACCOUNT_EMAIL_REQUIRED = False  # Désactive l'utilisation obligatoire de l'email



ACCOUNT_EMAIL_VERIFICATION = "none"  

LOGIN_REDIRECT_URL = "/"  #redirection vers accueil quand on se connecte 

# Configuration de WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuration HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Mise à jour de CORS pour HTTPS
CORS_ORIGIN_WHITELIST = ['https://localhost:8080'] + os.getenv('CORS_ORIGIN_WHITELIST', '').split(',')