from django.shortcuts import redirect
from django.urls import reverse

class SaaSControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # 1. Rotas que não exigem login (Institucional, Auth e Webhook do Stripe)
        rotas_publicas = [
            reverse('narrativa:home'),
            reverse('narrativa:login'),
            reverse('narrativa:logout'),
            reverse('narrativa:criarconta'),
            reverse('narrativa:planos'),
            reverse('narrativa:stripe_webhook'),
        ]

        # Libera rotas públicas, o painel Django Admin (que tem segurança própria)
        # e o mais importante: TODAS as rotas do paciente jogando a jornada.
        if (path in rotas_publicas or
            path.startswith('/jornada/') or
            path.startswith('/cena/') or
            path.startswith('/admin/')):
            return self.get_response(request)

        # ==========================================
        # SE CHEGOU AQUI, É ÁREA RESTRITA DA CLÍNICA
        # ==========================================

        # 2. Verifica se está logado
        if not request.user.is_authenticated:
            return redirect('narrativa:login')

        # 3. Verifica se tem assinatura ativa
        if hasattr(request.user, 'clinica') and request.user.clinica:
            if not request.user.clinica.assinatura_ativa:
                # Se NÃO pagou, e NÃO está tentando acessar as páginas de checkout, trava ele
                if not (path.startswith('/planos/') or path.startswith('/checkout/') or path.startswith('/sucesso/')):
                    return redirect('narrativa:planos')

        return self.get_response(request)