from .models import Narrativa, ConfiguracaoClinica # Adicionado ConfiguracaoClinica
import logging # Adicionado para logging

def lista_narrativas_recentes(request):
    lista_narrativas = Narrativa.objects.all().order_by('-data_criacao')[0:8]
    if lista_narrativas:
        narrativa_destaque = lista_narrativas[0]
    else:
        narrativa_destaque = None
    return {"lista_narrativas_recentes": lista_narrativas, "narrativa_destaque": narrativa_destaque}

def lista_narrativas_emalta(request):
    lista_narrativas = Narrativa.objects.all().order_by('-visualizacoes')[0:8]
    return {"lista_narrativas_emalta": lista_narrativas}

# --- FUNÇÃO ADICIONADA PARA O LOGO ---
def logo_clinica(request):
    try:
        # Tenta pegar o logo. Cria o objeto de config se for a primeira vez.
        config, created = ConfiguracaoClinica.objects.get_or_create(id=1)
        if config.logo:
            return {'logo_url': config.logo.url}
    except Exception as e:
        # Se o banco não estiver migrado (ou outro erro), não quebra o site
        logging.warning(f"Não foi possível carregar o logo da clínica: {e}")
        pass
    return {'logo_url': None}