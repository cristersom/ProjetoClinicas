from django.shortcuts import redirect
from django.urls import reverse


class SaaSControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # URLs que qualquer pessoa (logada ou não) pode acessar
        exempt_urls = [
            reverse('narrativa:home'),
            reverse('narrativa:login'),
            reverse('narrativa:criarconta'),
            reverse('narrativa:planos'),  # Liberado para o público
            reverse('narrativa:stripe_webhook'),
            reverse('narrativa:sucesso_pagamento'),
            '/admin/',
        ]

        # Se for uma das URLs livres, deixa passar
        if any(path.startswith(url) for url in exempt_urls):
            return self.get_response(request)

        # Se estiver logado mas sem assinatura, força ir para planos
        if request.user.is_authenticated:
            if not request.user.is_superuser:
                clinica = getattr(request.user, 'clinica', None)
                if not clinica or not clinica.assinatura_ativa:
                    if path != reverse('narrativa:planos'):
                        return redirect('narrativa:planos')

        return self.get_response(request)