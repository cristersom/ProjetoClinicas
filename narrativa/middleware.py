from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class SaaSControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Bloqueio de acesso para administradores sem assinatura ativa
        if request.user.is_authenticated and not request.user.is_superuser:
            if not request.user.clinica or not request.user.clinica.assinatura_ativa:
                allowed = [reverse('narrativa:logout'), reverse('narrativa:login')]
                if not any(path.startswith(p) for p in allowed) and not path.startswith('/static/'):
                    # Redirecionar para página de pagamento ou aviso (opcional)
                    pass

        # Controle de Termos para Pacientes
        if path.startswith('/paciente/'):
            key = getattr(settings, 'TERMOS_ACEITOS_KEY', 'termo_aceite_session')
            if not request.user.is_authenticated and not request.session.get(key, False):
                if not path.startswith(reverse('narrativa:ler_termos')):
                    return redirect('narrativa:ler_termos')

        return self.get_response(request)