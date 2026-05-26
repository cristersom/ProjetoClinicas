import os
from pathlib import Path
import dj_database_url
from django.urls import reverse_lazy

BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURANÇA ---
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-chave-temporaria-de-seguranca')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['narrativasclinicas.com.br', 'narrativas-clinicas-0108a6c374ea.herokuapp.com', 'localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['https://narrativasclinicas.com.br', 'https://narrativas-clinicas-0108a6c374ea.herokuapp.com']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True


# --- UNFOLD ADMIN (Substitui o Jazzmin) ---
UNFOLD = {
    "SITE_TITLE": "Narrativas Clínicas",
    "SITE_HEADER": "Narrativas Clínicas",
    "SITE_URL": "/",
    "COLORS": {
        "primary": {
            "50": "240 253 250",
            "100": "204 251 241",
            "200": "153 246 228",
            "300": "94 234 212",
            "400": "45 212 191",
            "500": "20 184 166",  # Cor Verde Água (#14b8a6)
            "600": "13 148 136",
            "700": "15 118 110",
            "800": "17 94 89",
            "900": "19 78 74",
            "950": "4 41 42",
        },
    },
    "SIDEBAR": {
        "show_search": False,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Principal",
                "items": [
                    {
                        "icon": "dashboard",
                        "title": "Dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": "Narrativa",
                "items": [
                    {
                        "icon": "auto_stories",
                        "title": "Narrativas",
                        "link": reverse_lazy("admin:narrativa_narrativa_changelist"),
                    },
                    {
                        "icon": "desktop_windows",
                        "title": "Cenas",
                        "link": reverse_lazy("admin:narrativa_cena_changelist"),
                    },
                    {
                        "icon": "assignment",
                        "title": "Questionários",
                        "link": reverse_lazy("admin:narrativa_questionario_changelist"),
                    },
                    {
                        "icon": "forum",
                        "title": "Respostas",
                        "link": reverse_lazy("admin:narrativa_resposta_changelist"),
                    },
                    {
                        "icon": "people",
                        "title": "Sessão Pacientes",
                        "link": reverse_lazy("admin:narrativa_sessaopaciente_changelist"),
                    },
                ],
            },
            {
                "title": "Atalhos",
                "items": [
                    {
                        "icon": "language",
                        "title": "Ver Site",
                        "link": "/",
                    },
                    {
                        "icon": "menu_book",
                        "title": "Manual do Sistema",
                        "link": reverse_lazy("narrativa:faq"),
                    },
                ]
            }
        ],
    },
}


# --- APPS ---
INSTALLED_APPS = [
    'unfold',  # Unfold SEMPRE no topo antes do admin
    'unfold.contrib.import_export',  # Integração do Unfold com o import_export
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'storages',
    'nested_admin',
    'crispy_forms',
    'crispy_bootstrap5',
    'import_export',
    'narrativa',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

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

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-2')

if AWS_STORAGE_BUCKET_NAME:
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
else:
    MEDIA_URL = '/media/'

AWS_DEFAULT_ACL = 'public-read'
AWS_QUERYSTRING_AUTH = False

STORAGES = {
    "default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

AUTH_USER_MODEL = 'narrativa.Usuario'
LOGIN_URL = 'narrativa:login'
LOGIN_REDIRECT_URL = 'narrativa:narrativas'
LOGOUT_REDIRECT_URL = 'narrativa:home'

STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'