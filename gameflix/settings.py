import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURANÇA ---
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-chave-temporaria-de-seguranca')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['narrativasclinicas.com.br', 'narrativas-clinicas-b7d6b38c0379.herokuapp.com', 'localhost',
                 '127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['https://narrativasclinicas.com.br', 'https://narrativas-clinicas-b7d6b38c0379.herokuapp.com']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# --- JAZZMIN CONFIGURAÇÕES VISUAIS E ÍCONES ---
JAZZMIN_SETTINGS = {
    "site_title": "Narrativas Clínicas",
    "site_header": "Narrativas Clínicas",
    "site_brand": "Administração",
    "welcome_sign": "Bem-vindo ao Painel da Clínica",
    "copyright": "Narrativas Clínicas",
    "search_model": ["narrativa.Narrativa", "narrativa.Paciente"],
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Ver Site", "url": "/", "new_window": True},
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "narrativa.Plano": "fas fa-star",
        "narrativa.Clinica": "fas fa-hospital",
        "narrativa.Usuario": "fas fa-user-md",
        "narrativa.Categoria": "fas fa-tags",
        "narrativa.Narrativa": "fas fa-book-medical",
        "narrativa.Cena": "fas fa-desktop",
        "narrativa.Questionario": "fas fa-clipboard-list",
        "narrativa.Resposta": "fas fa-comments",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "show_sidebar": True,
    "navigation_expanded": True,
    "order_with_respect_to": ["narrativa", "narrativa.Narrativa", "narrativa.Cena", "narrativa.Questionario"],
}
JAZZMIN_UI_TWEAKS = {"theme": "pulse", "dark_mode_theme": "darkly"}

# --- APPS ---
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # AWS S3
    'storages',

    # Ferramentas Admin
    'nested_admin',
    'crispy_forms',
    'crispy_bootstrap5',

    # Seu App Principal
    'narrativa',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# --- MIDDLEWARE ---
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
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gameflix.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
}
if not DATABASES['default']:
    DATABASES['default'] = {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# --- ARQUIVOS ESTÁTICOS ---
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# --- AMAZON S3 PARA MÍDIAS (UPLOADS) ---
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-2')

# Isso garante que a URL gerada seja pública e sem expiração temporária
if AWS_STORAGE_BUCKET_NAME:
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
else:
    MEDIA_URL = '/media/'

AWS_DEFAULT_ACL = 'public-read'
AWS_QUERYSTRING_AUTH = False

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

AUTH_USER_MODEL = 'narrativa.Usuario'
LOGIN_URL = 'narrativa:login'
LOGIN_REDIRECT_URL = 'narrativa:narrativas'
LOGOUT_REDIRECT_URL = 'narrativa:home'

STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'