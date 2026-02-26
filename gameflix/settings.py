import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-chave-temporaria')
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['narrativasclinicas.com.br', 'www.narrativasclinicas.com.br', 'narrativas-clinicas-0108a6c374ea.herokuapp.com', '127.0.0.1', '*']

# Segurança CSRF e Cookies para HTTPS
CSRF_TRUSTED_ORIGINS = [
    'https://narrativasclinicas.com.br',
    'https://www.narrativasclinicas.com.br',
    'https://narrativas-clinicas-0108a6c374ea.herokuapp.com'
]
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'jazzmin', # Jazzmin antes do admin
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

# Modelo de Usuário Customizado (Obrigatório para seu models.py funcionar)
AUTH_USER_MODEL = 'narrativa.Usuario'

DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600
    )
}

STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', 'pk_test_sua_chave')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', 'sk_test_sua_chave')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME', 'du066v6vj'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
}

JAZZMIN_SETTINGS = {
    "site_title": "Narrativas Clínicas",
    "site_header": "Narrativas Clínicas",
    "site_brand": "Administração",
    "welcome_sign": "Gestão Clínica",
    "show_sidebar": True,
    "navigation_expanded": True,
    "order_with_respect_to": ["narrativa.Clinica", "narrativa.Narrativa", "narrativa.Usuario"],

    # Ícones para os itens do menu lateral
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.Group": "fas fa-users",
        "narrativa.Usuario": "fas fa-user",
        "narrativa.Clinica": "fas fa-clinic-medical",
        "narrativa.Narrativa": "fas fa-book-medical",
        "narrativa.Categoria": "fas fa-tags",
        "narrativa.Cena": "fas fa-image",
        "narrativa.LogVisitaCena": "fas fa-history",
        "narrativa.Questionario": "fas fa-poll-h",
        "narrativa.Resposta": "fas fa-comment-dots",
        "narrativa.SessaoPaciente": "fas fa-user-clock",
    },

    # Links customizados no topo (Dashboard)
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Dashboard", "url": "narrativa:dashboard_admin"},  # Garanta que essa rota existe em narrativa/urls.py
    ],
}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'