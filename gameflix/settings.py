# gameflix/settings.py

# ... (Mantenha as configurações de banco de dados e Cloudinary)

JAZZMIN_SETTINGS = {
    "site_title": "Narrativas Clínicas",
    "site_header": "Narrativas Clínicas",
    "site_brand": "Narrativas Clínicas",
    "welcome_sign": "Gestão de Jornadas",
    "copyright": "Narrativas Clínicas © 2026",
    "search_model": ["narrativa.Narrativa", "narrativa.Usuario"],

    # Ícones da Esquerda - Personalizados para não serem apenas bolinhas
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "narrativa.Usuario": "fas fa-user-md",
        "narrativa.Clinica": "fas fa-hospital",
        "narrativa.Narrativa": "fas fa-book-medical",
        "narrativa.Cena": "fas fa-play-circle",
        "narrativa.Questionario": "fas fa-list-alt",
        "narrativa.Resposta": "fas fa-comment-medical",
        "narrativa.SessaoPaciente": "fas fa-history",
        "narrativa.LogVisitaCena": "fas fa-eye",
        "narrativa.Categoria": "fas fa-tags",
    },
    # Faz com que os ícones apareçam sempre, sem precisar passar o mouse
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
}

# Cores mais sóbrias para não ficar "feio" ou carregado
JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",  # Tema mais limpo e moderno
    "dark_mode_theme": None,  # Desativa o modo escuro automático se preferir o clássico
    "navbar": "navbar-dark bg-dark",
    "accent": "accent-primary",
    "sidebar": "sidebar-dark-primary",
}