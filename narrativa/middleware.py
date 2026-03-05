from django.shortcuts import redirect
from django.urls import reverse

class SaaSControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Lista de URLs que NUNCA devem ser bloqueadas
        exempt_urls = [
            reverse('narrativa:planos'),
            reverse('narrativa:home'),
            reverse('narrativa:criarconta'),
            reverse('narrativa:stripe_webhook'),
            '/admin/', # Importante para você não ficar trancado fora
        ]

        # Se a URL atual estiver na lista ou for um arquivo estático, permite
        if any(request.path.startswith(url) for url in exempt_urls) or request.path.startswith('/static/'):
            return self.get_response(request)

        # 2. Lógica de bloqueio para usuários logados sem assinatura
        if request.user.is_authenticated:
            # Verifica se a clínica do usuário tem assinatura ativa
            # (Ajuste conforme o nome do campo no seu modelo Clinica)
            if not request.user.clinica.assinatura_ativa:
                if request.path != reverse('narrativa:planos'):
                    return redirect('narrativa:planos')

        return self.get_response(request)