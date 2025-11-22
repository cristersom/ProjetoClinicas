from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['127.0.0.1', '.herokuapp.com']

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
    'narrativa.middleware.PatientAccessMiddleware',
]

ROOT_URLCONF = 'gameflix.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'narrativa.context.lista_narrativas_recentes',
                'narrativa.context.lista_narrativas_emalta',
                'narrativa.context.dados_clinica',
            ],
        },
    },
]

WSGI_APPLICATION = 'gameflix.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    )
}

AUTH_USER_MODEL = "narrativa.usuario"
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

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = 'narrativa:narrativas'
LOGIN_URL = 'narrativa:login'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

JAZZMIN_SETTINGS = {
    "site_title": "Administração Clínica",
    "site_header": "Clínica Admin",
    "welcome_sign": "Bem-vindo(a) à Administração",
    "copyright": "Minha Clínica Ltd",

    "topmenu_links": [
        {"name": "Ver Site", "url": "/", "new_window": True},

        # --- LINK NOVO: DASHBOARD ---
        {
            "name": "Dashboard",
            "url": "narrativa:dashboard_admin",
            "icon": "fas fa-tachometer-alt"
        },

        {"app": "narrativa"},
        {
            "name": "Ajuda",
            "url": "narrativa:admin_faq",
            "icon": "fas fa-question-circle",
            "new_window": True
        },
    ],

    "order_with_respect_to": [
        "narrativa.Narrativa",
        "narrativa.Cena",
        "narrativa.Questionario",
        "narrativa.Resposta",
        "narrativa.Categoria",
        "narrativa.ConfiguracaoClinica",
        "narrativa.SessaoPaciente",
        "narrativa.Usuario",
    ],

    "apps": {
        "narrativa": "Gestão da Jornada",
    },

    "models": {
        "narrativa.ConfiguracaoClinica": {
            "verbose_name": "Logotipo",
            "verbose_name_plural": "Logotipo",
        }
    },

    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "narrativa.Narrativa": "fas fa-book-open",
        "narrativa.Cena": "fas fa-film",
        "narrativa.Escolha": "fas fa-code-branch",
        "narrativa.Questionario": "fas fa-clipboard-list",
        "narrativa.Pergunta": "fas fa-question-circle",
        "narrativa.Resposta": "fas fa-comment",
        "narrativa.SessaoPaciente": "fas fa-user-clock",
        "narrativa.Usuario": "fas fa-user-shield",
        "narrativa.Categoria": "fas fa-tags",
        "narrativa.ConfiguracaoClinica": "fas fa-image",
    },

    "hide_models": [
        "narrativa.opcaoresposta",
        "auth.permission",
    ],
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}