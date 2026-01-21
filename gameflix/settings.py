from pathlib import Path
import os
import dj_database_url

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# SEGURANÇA: Mantenha a chave secreta em variáveis de ambiente no Heroku
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-substitua-isso-em-producao')

# DEBUG deve ser False em produção no Heroku
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# ALLOWED_HOSTS configurado para aceitar o Heroku e domínios customizados
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.herokuapp.com']

# Definição dos Apps instalados
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
    'cloudinary_storage',
    'cloudinary',
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
    'narrativa.middleware.SaaSControlMiddleware', # Middleware ajustado para Multi-Tenant
]

ROOT_URLCONF = 'gameflix.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'narrativa.context.lista_narrativas_recentes',
                'narrativa.context.lista_narrativas_emalta',
                'narrativa.context.dados_clinica', # Contexto para logos das clínicas
            ],
        },
    },
]

WSGI_APPLICATION = 'gameflix.wsgi.application'

# BANCO DE DADOS: PostgreSQL para Heroku e SQLite para desenvolvimento local
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600
    )
}

# Modelo de Usuário Customizado
AUTH_USER_MODEL = "narrativa.usuario"

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internacionalização
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Arquivos Estáticos e Mídia
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'

# ARMAZENAMENTO: Cloudinary para mídia (logos/thumbs) e WhiteNoise para estáticos
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Configurações do Cloudinary (pegas do ambiente Heroku)
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = 'narrativa:narrativas'
LOGIN_URL = 'narrativa:login'

# Configurações de UI (Crispy Forms)
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# JAZZMIN: Configuração do Painel Administrativo SaaS
JAZZMIN_SETTINGS = {
    "site_title": "SaaS Clínica Interativa",
    "site_header": "Gestão Clínica",
    "site_brand": "Painel SaaS",
    "welcome_sign": "Bem-vindo ao Gerenciador de Jornadas",
    "copyright": "Clínica Interativa SaaS",
    "topmenu_links": [
        {"name": "Ver Site", "url": "/", "new_window": True},
        {"name": "Dashboard", "url": "narrativa:dashboard_admin", "icon": "fas fa-tachometer-alt"},
        {"app": "narrativa"},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "narrativa.Clinica": "fas fa-hospital",
        "narrativa.Narrativa": "fas fa-book-open",
        "narrativa.Cena": "fas fa-film",
        "narrativa.Questionario": "fas fa-clipboard-list",
        "narrativa.SessaoPaciente": "fas fa-user-clock",
    },
}

JAZZMIN_UI_TWEAKS = {
    "theme": "default",
    "dark_mode_theme": "darkly",
    "navbar": "navbar-dark",
    "accent": "accent-teal",
}