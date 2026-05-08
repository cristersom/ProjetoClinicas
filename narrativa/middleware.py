import stripe
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class SaaSControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # 1. INJEÇÃO DE DADOS
        request.clinica_realtime = None
        request.limite_atingido = False

        if request.user.is_authenticated and hasattr(request.user, 'clinica') and request.user.clinica:
            from narrativa.models import Clinica, Narrativa
            try:
                clinica = Clinica.objects.get(id=request.user.clinica.id)
                request.clinica_realtime = clinica

                # Sincronização com Stripe
                if clinica.stripe_customer_id and not request.session.get('stripe_synced'):
                    stripe.api_key = settings.STRIPE_SECRET_KEY
                    try:
                        # Liga para o Stripe verificar se existe alguma assinatura ativa
                        subs = stripe.Subscription.list(customer=clinica.stripe_customer_id, status='active', limit=1)
                        tem_plano_ativo = len(subs.data) > 0
                        if clinica.assinatura_ativa != tem_plano_ativo:
                            clinica.assinatura_ativa = tem_plano_ativo
                            clinica.save()
                        # Salva na sessão para não ficar fazendo essa consulta lenta a cada clique
                        request.session['stripe_synced'] = True
                    except Exception:
                        pass

                # Cálculo de limites
                if clinica.plano_atual:
                    try:
                        limite = int(clinica.plano_atual.limite_narrativas)
                    except (ValueError, TypeError):
                        limite = 0
                    qtd_atual = Narrativa.objects.filter(clinica=clinica).count()
                    request.limite_atingido = (qtd_atual >= limite)
            except Clinica.DoesNotExist:
                pass

        # 2. ROTAS PÚBLICAS
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

        # 3. BLINDAGEM DO ADMINISTRADOR (Bloqueia apenas AÇÕES, não a visão)
        if path.startswith('/admin/'):
            if request.user.is_authenticated and not request.user.is_superuser:
                clinica = request.clinica_realtime
                if clinica:
                    is_admin_action = ('/add/' in path or '/change/' in path or '/delete/' in path)
                    is_post_method = request.method in ['POST', 'PUT', 'DELETE', 'PATCH']

                    if not clinica.assinatura_ativa and (is_admin_action or is_post_method):
                        messages.error(request,
                                       'Não identificamos seu pagamento, realize a renovação para continuar editando.')
                        return redirect('/admin/')

                    if '/admin/narrativa/narrativa/add/' in path and request.limite_atingido:
                        messages.error(request, 'Limite de plano atingido.')
                        return redirect('/admin/')

            return self.get_response(request)

        # 4. ÁREA RESTRITA FRONTEND
        if not request.user.is_authenticated:
            return redirect('narrativa:login')

        return self.get_response(request)