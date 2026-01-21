from .models import Narrativa, Clinica

def dados_clinica(request):
    """Injeta o logo da clínica ativa na navbar."""
    if request.user.is_authenticated and hasattr(request.user, 'clinica') and request.user.clinica:
        return {'logo_url': request.user.clinica.logo.url if request.user.clinica.logo else None}
    return {'logo_url': None}

def lista_narrativas_recentes(request):
    """Filtra narrativas pela clínica do usuário logado."""
    qs = Narrativa.objects.all()
    if request.user.is_authenticated and hasattr(request.user, 'clinica') and request.user.clinica:
        qs = qs.filter(clinica=request.user.clinica)
    return {"lista_narrativas_recentes": qs.order_by('-data_criacao')[:8]}

def lista_narrativas_emalta(request):
    """Filtra narrativas populares pela clínica."""
    qs = Narrativa.objects.all()
    if request.user.is_authenticated and hasattr(request.user, 'clinica') and request.user.clinica:
        qs = qs.filter(clinica=request.user.clinica)
    return {"lista_narrativas_emalta": qs.order_by('-visualizacoes')[:8]}