from django.shortcuts import redirect
from django.urls import reverse

class SaaSControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # 1. Rotas Exatas que não exigem login
        rotas_publicas = [
            reverse('narrativa:home'),
            reverse('narrativa:login'),
            reverse('narrativa:logout'),
            reverse('narrativa:criarconta'),
            reverse('narrativa:planos'),
            reverse('narrativa:stripe_webhook'),
            reverse('narrativa:sucesso_pagamento'), # Rota de Sucesso liberada!
        ]

        # 2. Rotas Dinâmicas que não exigem login (Iniciam com...)
        if (path in rotas_publicas or
            path.startswith('/checkout/') or # O Checkout não exige login (Frictionless)!
            path.startswith('/jornada/') or  # O paciente jogando
            path.startswith('/cena/') or     # Cenas e questionários
            path.startswith('/admin/')):     # Painel tem segurança própria
            return self.get_response(request)

        # ==========================================
        # SE CHEGOU AQUI, É ÁREA RESTRITA DA CLÍNICA
        # ==========================================

        # 3. Verifica se a Clínica está logada
        if not request.user.is_authenticated:
            return redirect('narrativa:login')

        # 4. Verifica se a Clínica pagou a assinatura
        if hasattr(request.user, 'clinica') and request.user.clinica:
            if not request.user.clinica.assinatura_ativa:
                return redirect('narrativa:planos')

        return self.get_response(request)