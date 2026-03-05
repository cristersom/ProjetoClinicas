import os
from pathlib import Path
import dj_database_url

# Caminhos básicos
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURANÇA (Ajustado) ---
# O Django usa DJANGO_SECRET_KEY. O Stripe usa STRIPE_SECRET_KEY.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-chave-temporaria-de-seguranca')

# No Heroku, definimos a variável DEBUG como 'True' para ver erros reais
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'narrativasclinicas.com.br',
    'narrativas-clinicas-b7d6b38c0379.herokuapp.com',
    'localhost',
    '127.0.0.1'
]

# --- APPS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'narrativa',  # Seu app principal
]

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Essencial para CSS/Imagens no Heroku
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Seu controle de assinatura (verifique se este arquivo existe em narrativa/middleware.py)
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

# --- BANCO DE DADOS (Configurado para Heroku Postgres) ---
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        ssl_require=True
    )
}

# Fallback para banco local (SQLite) caso o Postgres não esteja disponível
if not DATABASES['default']:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

# --- SENHAS ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- INTERNACIONALIZAÇÃO ---
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# --- ARQUIVOS ESTÁTICOS (WhiteNoise) ---
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- CONFIGURAÇÃO DE USUÁRIO CUSTOMIZADO ---
AUTH_USER_MODEL = 'narrativa.Usuario'
LOGIN_URL = 'narrativa:home'
LOGIN_REDIRECT_URL = 'narrativa:narrativas'
LOGOUT_REDIRECT_URL = 'narrativa:home'

# --- STRIPE CONFIGURATION (Lendo do Heroku Config) ---
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'