import os
from pathlib import Path
import dj_database_url

# Caminhos básicos
BASE_DIR = Path(__file__).resolve().parent.parent

# Segurança básica
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-chave-temporaria')
DEBUG = True # Ativado para identificar erros de template remanescentes

ALLOWED_HOSTS = ['narrativasclinicas.com.br', 'www.narrativasclinicas.com.br', 'narrativas-clinicas.herokuapp.com', '127.0.0.1', '*']

# Apps instalados
INSTALLED_APPS = [
    'jazzmin', # Jazzmin sempre antes do admin
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

# Middleware
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

# Templates
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

# Banco de Dados (Heroku utiliza dj_database_url)
DATABASES = {
    'default': dj_database_url.config(default='sqlite:///db.sqlite3', conn_max_age=600)
}

# Modelo de Usuário Customizado
AUTH_USER_MODEL = 'narrativa.Usuario'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- CONFIGURAÇÕES DE SEGURANÇA (PARA CLOUDFLARE/HEROKU) ---
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
CSRF_TRUSTED_ORIGINS = ['https://narrativasclinicas.com.br', 'https://www.narrativasclinicas.com.br']

# Mantemos False para evitar o loop 301 infinito com o Cloudflare
SECURE_SSL_REDIRECT = False

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# --- ARQUIVOS ESTÁTICOS E MEDIA ---
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

# --- INTEGRAÇÕES (STRIPE) ---
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

LOGIN_REDIRECT_URL = 'narrativa:narrativas'
LOGOUT_REDIRECT_URL = 'narrativa:home'
LOGIN_URL = 'narrativa:home'

# --- INTERFACE ADMIN ---
JAZZMIN_SETTINGS = {
    "site_title": "Narrativas Clínicas",
    "site_header": "Narrativas Clínicas",
    "site_brand": "Administração",
    "show_sidebar": True,
    "navigation_expanded": True,
}

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"