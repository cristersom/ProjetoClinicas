from .models import Narrativa, ConfiguracaoClinica


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


def dados_clinica(request):
    try:
        # Busca a configuração (que sempre será pk=1)
        config = ConfiguracaoClinica.objects.get(pk=1)
        if config.logo:
            return {'logo_url': config.logo.url}
    except ConfiguracaoClinica.DoesNotExist:
        pass

    return {'logo_url': None}