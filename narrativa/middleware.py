from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class SaaSControlMiddleware:
    """Controla o acesso de pacientes (termos) e administradores (assinatura)."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # 1. LIBERAR ACESSO: Ignora rotas críticas para não travar o login ou o site
        # Liberamos o Admin, estáticos, mídias e a própria home
        if any(path.startswith(p) for p in ['/admin/', '/static/', '/media/', '/login/', '/logout/']):
            return self.get_response(request)

        # 2. BLOQUEIO POR ASSINATURA: Para administradores de clínica logados
        if request.user.is_authenticated and not request.user.is_superuser:
            # Se o usuário não tiver clínica ou a assinatura estiver inativa
            if not getattr(request.user, 'clinica', None) or not request.user.clinica.assinatura_ativa:
                # Permite apenas o logout se estiver bloqueado
                if path != reverse('narrativa:logout'):
                    # Opcional: Redirecionar para uma página de "Assine Já"
                    pass

        # 3. ACEITE DE TERMOS: Para a jornada do paciente
        if path.startswith('/paciente/'):
            key = getattr(settings, 'TERMOS_ACEITOS_KEY', 'termo_aceite_session')
            if not request.user.is_authenticated and not request.session.get(key, False):
                if not path.startswith(reverse('narrativa:ler_termos')):
                    return redirect('narrativa:ler_termos')

        return self.get_response(request)