import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-chave-temporaria')
DEBUG = True

ALLOWED_HOSTS = ['narrativasclinicas.com.br', 'www.narrativasclinicas.com.br', 'narrativas-clinicas.herokuapp.com', '127.0.0.1', '*']

INSTALLED_APPS = [
    'jazzmin', # Deve ser o primeiro
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
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
        'APP_DIRS': True, # Vital para o Jazzmin
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

# --- SEGURANÇA ---
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
CSRF_TRUSTED_ORIGINS = ['https://narrativasclinicas.com.br', 'https://www.narrativasclinicas.com.br']
SECURE_SSL_REDIRECT = False

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

# --- JAZZMIN (ÍCONES E VISUAL) ---
JAZZMIN_SETTINGS = {
    "site_title": "Narrativas Clínicas",
    "site_brand": "Administração",
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "narrativa.Usuario": "fas fa-user",
        "narrativa.Clinica": "fas fa-clinic-medical",
        "narrativa.Narrativa": "fas fa-book-medical",
        "narrativa.Cena": "fas fa-image",
        "narrativa.Questionario": "fas fa-poll-h",
        "narrativa.Resposta": "fas fa-comment-dots",
        "narrativa.SessaoPaciente": "fas fa-user-clock",
        "narrativa.LogVisitaCena": "fas fa-history",
        "narrativa.Categoria": "fas fa-tags",
    },
    "topmenu_links": [
        {"name": "Home", "url": "admin:index"},
        {"name": "Dashboard Visual", "url": "narrativa:dashboard_admin"},
    ],
}

JAZZMIN_UI_TWEAKS = {"theme": "flatly", "sidebar": "sidebar-dark-primary"}

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"