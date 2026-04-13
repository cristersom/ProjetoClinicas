import os
from pathlib import Path

# Constrói os caminhos dentro do projeto como: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================================
# SEGURANÇA E AMBIENTE
# ==========================================
# O ideal em produção (Heroku) é puxar a chave das variáveis de ambiente.
# Se não encontrar, usa uma chave padrão para não quebrar no seu PC.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-sua-chave-secreta-aqui')

# O DEBUG deve ser False no Heroku para o WhiteNoise e a segurança funcionarem.
# Como você disse que já está no ar, deixamos dinâmico ou False.
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Libera o acesso para o seu domínio do Heroku e domínio local
ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1']
# Em produção rigorosa, troque '*' pelo 'seusite.herokuapp.com'


# ==========================================
# APLICATIVOS INSTALADOS
# ==========================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',

    # WhiteNoise para gerenciar arquivos estáticos de forma eficiente
    'whitenoise.runserver_nostatic',

    'django.contrib.staticfiles',

    # Bibliotecas de Terceiros que o seu painel Admin utiliza
    'nested_admin',
    'import_export',

    # Seu aplicativo principal
    'narrativa',
]

# ==========================================
# MIDDLEWARES (A "Peneira" do Sistema)
# ==========================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # O WhiteNoise OBRIGATORIAMENTE deve ser o segundo na lista
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # O "Segurança da Porta" do seu SaaS para bloquear áreas restritas
    'narrativa.middleware.SaaSControlMiddleware',
]

ROOT_URLCONF = 'gameflix.urls'  # Altere 'gameflix' se a pasta principal tiver outro nome

# ==========================================
# TEMPLATES E RENDERIZAÇÃO
# ==========================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # Caso tenha templates globais
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

WSGI_APPLICATION = 'gameflix.wsgi.application'  # Altere 'gameflix' se a pasta principal tiver outro nome

# ==========================================
# BANCO DE DADOS
# ==========================================
# Por padrão usa o SQLite local. No Heroku, recomenda-se usar o dj-database-url,
# mas deixaremos o padrão para garantir que funcione de imediato sem quebrar.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==========================================
# USUÁRIO CUSTOMIZADO E AUTENTICAÇÃO
# ==========================================
AUTH_USER_MODEL = 'narrativa.Usuario'

# Configurações de redirecionamento de Login
LOGIN_URL = 'narrativa:login'
LOGIN_REDIRECT_URL = 'narrativa:narrativas'  # Redireciona para o painel após o login
LOGOUT_REDIRECT_URL = 'narrativa:home'

# ==========================================
# VALIDAÇÃO DE SENHAS E INTERNACIONALIZAÇÃO
# ==========================================
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

# ==========================================
# ARQUIVOS ESTÁTICOS E MÍDIA (WhiteNoise + Heroku)
# ==========================================
STATIC_URL = 'static/'

# Local onde o Django vai reunir todos os arquivos na hora de subir pro Heroku
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Onde os seus arquivos HTML, CSS, JS e Imagens da homepage estão durante o desenvolvimento
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'narrativa', 'static'),
]

# Configuração de performance e cache do WhiteNoise (Garante que o Heroku leia tudo)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Configuração de Mídia (Arquivos e imagens enviadas pelo painel Admin)
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==========================================
# INTEGRAÇÃO STRIPE (Variáveis do Heroku)
# ==========================================
# Busque essas chaves nas "Config Vars" do Heroku em produção
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', 'sua_chave_publica_aqui')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sua_chave_secreta_aqui')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'seu_webhook_secret_aqui')