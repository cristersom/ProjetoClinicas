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

                # Calcula se o limite foi atingido para usar no Frontend e Backend
                if clinica.plano_atual:
                    try:
                        limite = int(
                            clinica.plano_atual.limite_narrativas) if clinica.plano_atual.limite_narrativas else 0
                    except (ValueError, TypeError):
                        limite = 0
                    qtd_atual = Narrativa.objects.filter(clinica=clinica).count()
                    request.limite_atingido = (qtd_atual >= limite)

            except Clinica.DoesNotExist:
                pass

        # 2. ROTAS PÚBLICAS E DO PACIENTE (LIVRES)
        rotas_publicas = [
            reverse('narrativa:home'),
            reverse('narrativa:login'),
            reverse('narrativa:logout'),
            reverse('narrativa:criarconta'),
            reverse('narrativa:planos'),
            reverse('narrativa:stripe_webhook'),
            reverse('narrativa:sucesso_pagamento'),
        ]

        if (path in rotas_publicas or
                path.startswith('/checkout/') or
                path.startswith('/jornada/') or
                path.startswith('/cena/') or
                path.startswith('/portal/')):
            return self.get_response(request)

        # 3. BLINDAGEM DO PAINEL DE ADMINISTRAÇÃO
        if path.startswith('/admin/'):
            if request.user.is_authenticated and not request.user.is_superuser:
                clinica = request.clinica_realtime

                if clinica:
                    is_admin_action = ('/add/' in path or '/change/' in path or '/delete/' in path)
                    is_post_method = request.method in ['POST', 'PUT', 'DELETE', 'PATCH']

                    if is_admin_action or is_post_method:
                        # TRAVA 1: Assinatura Cancelada pelo Stripe
                        if not clinica.assinatura_ativa:
                            messages.error(request,
                                           'Bloqueado: Sua assinatura está inativa ou cancelada. Regularize para voltar a editar.')
                            return redirect('/admin/')

                        # TRAVA 2: Limite de Narrativas Atingido (Só bloqueia a ROTA de Adicionar Narrativa)
                        if '/admin/narrativa/narrativa/add/' in path:
                            if request.limite_atingido:
                                messages.error(request,
                                               'Bloqueado: Você atingiu o limite de narrativas do seu plano atual. Faça um Upgrade.')
                                return redirect('/admin/')

            return self.get_response(request)

        # 4. BLINDAGEM DA ÁREA RESTRITA FRONTEND
        if not request.user.is_authenticated:
            return redirect('narrativa:login')

        if request.clinica_realtime and not request.clinica_realtime.assinatura_ativa:
            return redirect('narrativa:planos')

        return self.get_response(request)