from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class SaaSControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # 1. INJEÇÃO DE DADOS EM TEMPO REAL E CÁLCULO DE LIMITE GLOBAL
        request.clinica_realtime = None
        request.limite_atingido = False

        if request.user.is_authenticated and hasattr(request.user, 'clinica') and request.user.clinica:
            from narrativa.models import Clinica, Narrativa
            try:
                clinica = Clinica.objects.get(id=request.user.clinica.id)
                request.clinica_realtime = clinica

                if clinica.plano_atual:
                    try:
                        limite = int(clinica.plano_atual.limite_narrativas)
                    except (ValueError, TypeError):
                        limite = 0
                    qtd_atual = Narrativa.objects.filter(clinica=clinica).count()
                    request.limite_atingido = (qtd_atual >= limite)
            except Clinica.DoesNotExist:
                pass

        # 2. ROTAS PÚBLICAS E DO PACIENTE (LIVRES)
        rotas_publicas = [
            reverse('narrativa:home'), reverse('narrativa:login'),
            reverse('narrativa:logout'), reverse('narrativa:criarconta'),
            reverse('narrativa:planos'), reverse('narrativa:stripe_webhook'),
            reverse('narrativa:sucesso_pagamento'),
        ]

        if (path in rotas_publicas or path.startswith('/checkout/') or
                path.startswith('/jornada/') or path.startswith('/cena/') or
                path.startswith('/portal/')):
            return self.get_response(request)

        # 3. BLINDAGEM DO PAINEL DE ADMINISTRAÇÃO
        if path.startswith('/admin/'):
            if request.user.is_authenticated and not request.user.is_superuser:
                clinica = request.clinica_realtime
                if clinica:
                    # Bloqueia QUALQUER ação de escrita (POST/DELETE) se o plano estiver inativo
                    is_post_method = request.method in ['POST', 'PUT', 'DELETE', 'PATCH']
                    if not clinica.assinatura_ativa and is_post_method:
                        messages.error(request, 'Operação Bloqueada: Assinatura inativa.')
                        return redirect('/admin/')

                    # Bloqueia especificamente a rota de adicionar narrativa se o limite estourou
                    if '/admin/narrativa/narrativa/add/' in path and request.limite_atingido:
                        messages.error(request, 'Limite atingido: Realize um upgrade.')
                        return redirect('/admin/')

        # 4. BLINDAGEM DA ÁREA RESTRITA FRONTEND
        if not request.user.is_authenticated:
            return redirect('narrativa:login')

        if request.clinica_realtime and not request.clinica_realtime.assinatura_ativa:
            return redirect('narrativa:planos')

        return self.get_response(request)