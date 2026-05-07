from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class SaaSControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # ==========================================
        # 1. ROTAS TOTALMENTE LIVRES (PACIENTES E PÚBLICO)
        # ==========================================
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

        # ==========================================
        # 2. BLINDAGEM DE ALTA SEGURANÇA (PAINEL ADMIN)
        # ==========================================
        if path.startswith('/admin/'):
            # Se for o dono do sistema (Superuser), passa livre
            if request.user.is_authenticated and not request.user.is_superuser:
                # Verifica se o usuário está tentando salvar, criar, editar ou deletar algo
                is_admin_action = ('/add/' in path or '/change/' in path or '/delete/' in path)
                is_post_method = request.method in ['POST', 'PUT', 'DELETE', 'PATCH']

                if is_admin_action or is_post_method:
                    if hasattr(request.user, 'clinica') and request.user.clinica:
                        from narrativa.models import Clinica
                        # BUSCA NO BANCO EM TEMPO REAL (Ignora o cache do login antigo)
                        try:
                            clinica_realtime = Clinica.objects.get(id=request.user.clinica.id)
                            if not clinica_realtime.assinatura_ativa:
                                messages.error(request,
                                               'Operação Bloqueada: Sua assinatura está inativa ou aguardando pagamento.')
                                return redirect('/admin/')  # Chuta o usuário de volta para o Dashboard
                        except Clinica.DoesNotExist:
                            pass

            # Se não estiver fazendo nenhuma ação proibida (ou se o block acima já rodou), segue o fluxo nativo do admin
            return self.get_response(request)

        # ==========================================
        # 3. ÁREA RESTRITA DO FRONTEND (RESTO DO SITE)
        # ==========================================
        if not request.user.is_authenticated:
            return redirect('narrativa:login')

        if hasattr(request.user, 'clinica') and request.user.clinica:
            from narrativa.models import Clinica
            # Busca em tempo real também para o frontend, garantindo que o cancelamento expulse o usuário na hora
            try:
                clinica_realtime = Clinica.objects.get(id=request.user.clinica.id)
                if not clinica_realtime.assinatura_ativa:
                    return redirect('narrativa:planos')
            except Clinica.DoesNotExist:
                pass

        return self.get_response(request)