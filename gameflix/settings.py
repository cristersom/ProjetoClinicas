# gameflix/settings.py (Trecho Final Ajustado)

# ... (mantenha o restante do arquivo igual)

# JAZZMIN: Configuração da Identidade Visual "Narrativas Clínicas"
JAZZMIN_SETTINGS = {
    "site_title": "Narrativas Clínicas",
    "site_header": "Narrativas Clínicas",
    "site_brand": "Narrativas Clínicas",
    "welcome_sign": "Bem-vindo ao Gerenciador de Jornadas",
    "copyright": "Narrativas Clínicas © 2026",

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