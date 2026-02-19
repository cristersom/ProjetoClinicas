import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-chave-temporaria')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'narrativa',
    'cloudinary',
    'cloudinary_storage',
    'crispy_forms',
    'crispy_bootstrap5',
    'import_export',
    'nested_admin',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Essencial para servir CSS/JS no Heroku
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'narrativa.middleware.SaaSControlMiddleware',
]

ROOT_URLCONF = 'gameflix.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'narrativa.context.dados_clinica',
            ],
        },
    },
]

WSGI_APPLICATION = 'gameflix.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(default='sqlite:///db.sqlite3', conn_max_age=600)
}

AUTH_USER_MODEL = 'narrativa.Usuario'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- CONFIGURAÇÃO DE ARQUIVOS ESTÁTICOS ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}

JAZZMIN_SETTINGS = {
    "site_title": "Narrativas Clínicas",
    "site_header": "Narrativas Clínicas",
    "site_brand": "Narrativas Clínicas",
    "welcome_sign": "Gestão de Jornadas",
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth.user": "fas fa-user",
        "narrativa.Usuario": "fas fa-user-md",
        "narrativa.Clinica": "fas fa-hospital",
        "narrativa.Narrativa": "fas fa-book-medical",
        "narrativa.Cena": "fas fa-play-circle",
        "narrativa.Questionario": "fas fa-list-alt",
    },
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "navbar": "navbar-dark bg-dark",
    "accent": "accent-primary",
    "sidebar": "sidebar-dark-primary",
}

# Adicione ou altere estas linhas no final do seu settings.py

# Redirecionamentos de Login
LOGIN_REDIRECT_URL = 'narrativa:narrativas'  # Após logar, vai para a lista de jornadas
LOGOUT_REDIRECT_URL = 'narrativa:login'      # Após sair, volta para a home/login
LOGIN_URL = 'narrativa:login'

# CONFIGURAÇÕES DO STRIPE
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', 'sua-chave-publica-aqui')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sua-chave-secreta-aqui')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'seu-segredo-webhook-aqui')

# gameflix/settings.py
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True  # Força o HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True