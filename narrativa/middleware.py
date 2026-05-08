from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class SaaSControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # 1. INJEÇÃO DE DADOS EM TEMPO REAL (Mata o cache e verifica o banco agora)
        request.clinica_realtime = None
        request.limite_atingido = False

        if request.user.is_authenticated and hasattr(request.user, 'clinica') and request.user.clinica:
            from narrativa.models import Clinica, Narrativa
            try:
                # Busca a clínica direto do banco para ignorar o que está guardado na sessão
                clinica = Clinica.objects.get(id=request.user.clinica.id)
                request.clinica_realtime = clinica

                # Verifica limites de plano
                if clinica.plano_atual:
                    try:
                        limite = int(clinica.plano_atual.limite_narrativas)
                    except (ValueError, TypeError):
                        limite = 0
                    qtd_atual = Narrativa.objects.filter(clinica=clinica).count()
                    request.limite_atingido = (qtd_atual >= limite)
            except Clinica.DoesNotExist:
                pass

        # 2. LIBERAÇÃO DE ROTAS PÚBLICAS (Página inicial, Login, Checkout e Pacientes)
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

        # 3. BLINDAGEM DO ADMINISTRADOR
        if path.startswith('/admin/'):
            if request.user.is_authenticated and not request.user.is_superuser:
                clinica = request.clinica_realtime
                if clinica:
                    # BLOQUEIO POR FALTA DE PAGAMENTO/CANCELAMENTO
                    # Se o usuário tentar SALVAR ou CRIAR algo (POST) e não tiver plano, barramos na hora
                    if not clinica.assinatura_ativa and request.method == 'POST':
                        messages.error(request, 'Ação Negada: Não reconhecemos o pagamento do seu plano.')
                        return redirect('/admin/')

                    # BLOQUEIO POR LIMITE DE PLANO
                    if '/add/' in path and 'narrativa' in path and request.limite_atingido:
                        messages.error(request, 'Limite atingido: Realize um upgrade para criar novas jornadas.')
                        return redirect('/admin/')

        # 4. BLINDAGEM DO FRONTEND (Área Logada do Site)
        if not request.user.is_authenticated:
            return redirect('narrativa:login')

        if request.clinica_realtime and not request.clinica_realtime.assinatura_ativa:
            # Se não pagou, mandamos direto para a página de planos
            return redirect('narrativa:planos')

        return self.get_response(request)