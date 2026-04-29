import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURANÇA E AMBIENTE ---
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-chave-temporaria-de-seguranca')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['narrativasclinicas.com.br', 'narrativas-clinicas-0108a6c374ea.herokuapp.com', 'localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['https://narrativasclinicas.com.br', 'https://narrativas-clinicas-0108a6c374ea.herokuapp.com']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# --- APPS ---
INSTALLED_APPS = [
    'jazzmin',
    'nested_admin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'narrativa',
    'crispy_forms',
    'crispy_bootstrap5',
    'import_export',
    'storages', # AWS S3
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
    'narrativa.middleware.SaaSControlMiddleware', # Seu Middleware B2B atualizado
]

ROOT_URLCONF = 'gameflix.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), os.path.join(BASE_DIR, 'narrativa', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'narrativa.context.dados_clinica',
                'narrativa.context.lista_narrativas_recentes',
                'narrativa.context.lista_narrativas_emalta',
            ],
        },
    },
]

WSGI_APPLICATION = 'gameflix.wsgi.application'

# --- BANCO DE DADOS ---
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3'),
        conn_max_age=600,
        ssl_require=False if DEBUG else True
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# --- USUÁRIO CUSTOMIZADO ---
AUTH_USER_MODEL = 'narrativa.Usuario'

# --- ARQUIVOS ESTÁTICOS ---
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# --- AMAZON S3 PARA MÍDIAS (UPLOADS) ---
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

if AWS_STORAGE_BUCKET_NAME:
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
else:
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- STRIPE E OUTROS ---
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', 'pk_test_sua_chave_publica')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_sua_chave_secreta')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_seu_segredo')
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
LOGIN_URL = 'narrativa:login'
LOGIN_REDIRECT_URL = 'narrativa:narrativas'

# --- JAZZMIN CONFIGURAÇÕES ---
JAZZMIN_SETTINGS = {
    "site_title": "Narrativas Clínicas",
    "site_header": "Narrativas Clínicas",
    "site_brand": "Administração",
    "welcome_sign": "Bem-vindo ao Painel da Clínica",
    "copyright": "Narrativas Clínicas",
    "search_model": ["narrativa.Narrativa"],
    "topmenu_links": [
        {"name": "Início", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Manual de Uso", "url": "narrativa:admin_faq", "icon": "fas fa-book-medical"},
        {"name": "Ver Portal", "url": "narrativa:home", "new_window": True},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": ["auth", "contenttypes", "sessions"],
    "hide_models": [],
    "order_with_respect_to": ["narrativa", "narrativa.Narrativa", "narrativa.Cena", "narrativa.Questionario"],
    "icons": {
        "auth.Group": "fas fa-users",
        "narrativa.usuario": "fas fa-user-md",
        "narrativa.narrativa": "fas fa-project-diagram",
        "narrativa.cena": "fas fa-tv",
        "narrativa.questionario": "fas fa-clipboard-list",
        "narrativa.categoria": "fas fa-tags",
        "narrativa.configuracaoclinica": "fas fa-cog",
        "narrativa.plano": "fas fa-star",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
}

JAZZMIN_UI_TWEAKS = {
    "theme": "default",
    "dark_mode_theme": "darkly",
}