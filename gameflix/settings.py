# settings.py

INSTALLED_APPS = [
    'jazzmin',  # <-- Adicione Jazzmin AQUI, antes de admin
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
    # Se você tinha identificado e comentado um tema antigo antes,
    # pode remover a linha comentada agora.
]

# ... (resto das configurações) ...

# --- Configurações Opcionais do Jazzmin (no final do arquivo) ---
JAZZMIN_SETTINGS = {
    # Título da janela do navegador (padrão: "Django admin")
    "site_title": "Administração Clínica",

    # Título na tela de login (padrão: "Django admin")
    "site_header": "Clínica Admin",

    # Logo na tela de login e na barra superior (opcional)
    # "site_logo": "caminho/para/seu/logo.png", # Precisa estar nos arquivos estáticos

    # Texto "Bem-vindo" (padrão: nome de usuário)
    "welcome_sign": "Bem-vindo(a) à Administração",

    # Copyright no rodapé
    "copyright": "Minha Clínica Ltd",

    # Links úteis na barra superior
    "topmenu_links": [
        # Link para a homepage do site (se houver)
        {"name": "Ver Site", "url": "/", "new_window": True},

        # Link para o app Narrativa
        {"app": "narrativa"},
    ],

    # Ícones para os modelos (usando Font Awesome)
    # https://fontawesome.com/v5/search
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
        "narrativa.Usuario": "fas fa-user-shield", # Modelo customizado
    },
    # Ocultar modelos que não precisam ser editados diretamente
    "hide_models": [
        "narrativa.opcaoresposta", # Editado via inline
        "auth.permission",
    ],
}

# --- Ajustes de UI opcionais ---
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark", # Ou "navbar-light", etc.
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary", # Ou sidebar-light-*, etc.
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default", # Temas: default, cerulean, cosmo, cyborg, darkly, flatly, journal, litera, lumen, lux, materia, minty, pulse, sandstone, simplex, sketchy, slate, solar, spacelab, superhero, united, yeti
    "dark_mode_theme": "darkly", # Tema a ser usado no modo escuro
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}