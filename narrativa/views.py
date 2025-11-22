# narrativa/views.py

# ... (Mantenha todos os imports existentes) ...
from django.db.models import Count, Q
from django.conf import settings

# Pega a chave de settings para consistência
TERMOS_ACEITOS_KEY = getattr(settings, 'TERMOS_ACEITOS_KEY', 'termo_aceite_session')


# --- NOVA VIEW: PERFIL DE SESSÃO DO PACIENTE (ANÔNIMO) ---

class SessaoPacientePerfilView(TemplateView):
    """Exibe o dashboard do paciente anônimo com progresso e selos de gamificação."""
    template_name = "perfil_paciente.html"  # Usaremos um novo nome para evitar conflito com 'perfil.html' (do Admin)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        session_key = self.request.session.session_key

        # 1. Obter Sessão e Perfil
        try:
            sessao = SessaoPaciente.objects.get(session_key=session_key)
            perfil_narrativa = sessao.narrativa_perfil
        except SessaoPaciente.DoesNotExist:
            sessao = None
            perfil_narrativa = None

        # 2. Rastreamento da Jornada e Questionários
        narrativas_vistas = LogVisitaCena.objects.filter(session_key=session_key).values(
            'narrativa_associada').annotate(
            cenas_vistas=Count('cena_visitada', distinct=True)
        )

        # 3. Cálculo de Progresso (Agregado)
        total_narrativas_completas = 0
        total_pesquisas_respondidas = 0
        total_pesquisas_disponiveis = 0
        total_narrativas_em_progresso = len(narrativas_vistas)

        # 3.1. Cálculo de Narrativa/Cena
        # A lógica de "Narrativas Concluídas" é complexa, vamos simplificar o cálculo 
        # para Contagem de Narrativas Acessadas e Progresso na Narrativa ATUAL.

        # Itera sobre todas as narrativas que o paciente tocou
        for item in narrativas_vistas:
            narrativa_id = item['narrativa_associada']
            try:
                narrativa_obj = Narrativa.objects.get(pk=narrativa_id)
                total_cenas_na_narrativa = narrativa_obj.cenas.count()

                # Se o número de cenas vistas for igual ao total, considera completa (simplificado)
                if item['cenas_vistas'] >= total_cenas_na_narrativa and total_cenas_na_narrativa > 0:
                    total_narrativas_completas += 1

                # 3.2. Cálculo de Questionários
                # Calcula quantas pesquisas estão disponíveis nas cenas que ele tocou
                cenas_tocadas_ids = LogVisitaCena.objects.filter(
                    session_key=session_key,
                    narrativa_associada_id=narrativa_id
                ).values_list('cena_visitada_id', flat=True).distinct()

                questionarios_disponiveis = Questionario.objects.filter(
                    cena_associada_id__in=cenas_tocadas_ids
                ).count()

                total_pesquisas_disponiveis += questionarios_disponiveis

            except Narrativa.DoesNotExist:
                continue

        # 3.3. Contagem de Respostas
        # Contamos o número REAL de respostas submetidas
        total_pesquisas_respondidas = Resposta.objects.filter(session_key=session_key).values(
            'pergunta__questionario').distinct().count()

        # 4. Definição do Perfil (Baseado na primeira narrativa)
        if perfil_narrativa:
            # EXEMPLO: Se a narrativa for 'Jornada Maria e João' (ID 5), Perfil: Família
            # Você precisa mapear a Categoria/ID para um nome de perfil gamificado (Exemplo: Aventureiro, Realizador)
            # Para o TCC, vamos usar um mapeamento simples:
            perfil_nome = perfil_narrativa.categoria.titulo if perfil_narrativa.categoria else "Aventureiro(a)"
        else:
            perfil_nome = "Observador(a)"

        # 5. Definição de Selos (Padrões baseados em métricas fáceis de checar)
        selos = []
        if total_pesquisas_respondidas >= 1:
            selos.append({'nome': 'Primeira Pesquisa', 'desc': 'Concluiu a primeira pesquisa de sessão.', 'icone': '✅'})
        if total_narrativas_completas >= 1:
            selos.append({'nome': 'Narrativa Mestra', 'desc': 'Concluiu uma jornada completa.', 'icone': '🏆'})
        if total_pesquisas_respondidas >= 5:
            selos.append({'nome': 'Mestre de Dados', 'desc': 'Contribuiu com 5+ pesquisas.', 'icone': '📊'})

        context.update({
            'sessao': sessao,
            'perfil_nome': perfil_nome,
            'total_narrativas_acessadas': total_narrativas_em_progresso,
            'total_narrativas_completas': total_narrativas_completas,
            'pesquisas_respondidas': total_pesquisas_respondidas,
            'pesquisas_disponiveis': total_pesquisas_disponiveis,
            'selos_conquistados': selos,

            # Dados para a barra de progresso principal (exemplo: todas as pesquisas)
            'progresso_geral_percentual': int(
                (total_pesquisas_respondidas / max(total_pesquisas_disponiveis, 1)) * 100),
        })

        return context