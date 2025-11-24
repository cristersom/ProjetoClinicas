# ... (Mantenha os imports anteriores) ...

@admin.register(Resposta)
class RespostaAdmin(ImportExportModelAdmin):
    # Desabilitamos os botões padrões de import/export para não confundir
    # Se quiser manter, remova as linhas abaixo, mas lembre-se de não usá-los para esse relatório
    change_list_template = "admin/change_list.html"

    list_display = ('id', 'get_questionario', 'pergunta', 'session_key_short', 'texto_resposta', 'data_resposta')
    list_filter = (NarrativaPerfilFilter, 'pergunta__questionario', 'data_resposta')
    search_fields = ('texto_resposta', 'session_key')

    # AQUI ESTÁ A SOLUÇÃO: Ação no menu dropdown
    actions = ['gerar_relatorio_tabela_excel']

    def session_key_short(self, obj):
        return obj.session_key[:8] + '...'

    session_key_short.short_description = 'Sessão'

    def get_questionario(self, obj):
        return obj.pergunta.questionario.titulo

    get_questionario.short_description = 'Questionário'

    @admin.action(description='📥 BAIXAR RELATÓRIO TABELA (1 Linha por Paciente)')
    def gerar_relatorio_tabela_excel(self, request, queryset):
        """
        Transforma as respostas em uma tabela onde:
        LINHAS = Pacientes (Sessões)
        COLUNAS = Perguntas
        """
        # 1. Descobrir quais questionários estão envolvidos na seleção
        ids_questionarios = queryset.values_list('pergunta__questionario', flat=True).distinct()

        # 2. Pegar TODAS as perguntas desses questionários (para criar as colunas do Excel)
        # Ordenamos para que as colunas fiquem na ordem correta
        perguntas_do_relatorio = Pergunta.objects.filter(
            questionario__id__in=ids_questionarios
        ).order_by('questionario__titulo', 'id')

        # 3. Pegar todas as sessões (pacientes) únicas da seleção
        sessoes_unicas = queryset.values_list('session_key', flat=True).distinct()

        # 4. Criar o Arquivo Excel em Memória
        dataset = Dataset()

        # --- CABEÇALHO (COLUNAS) ---
        # Colunas fixas
        header_row = ['ID Sessão', 'Data da Resposta', 'Perfil do Paciente']

        # Colunas Dinâmicas (As Perguntas)
        mapa_pergunta_coluna = {}  # Dicionário para saber em qual coluna colocar a resposta
        col_index = 3  # Começa na coluna 3 (0, 1, 2 são as fixas)

        for p in perguntas_do_relatorio:
            # Texto da coluna será o texto da pergunta
            titulo_coluna = f"[{p.questionario.titulo}] {p.texto_pergunta}"
            header_row.append(titulo_coluna)
            mapa_pergunta_coluna[p.id] = col_index
            col_index += 1

        dataset.headers = header_row

        # --- CORPO (LINHAS) ---
        for sessao in sessoes_unicas:
            # Para cada paciente, criamos uma linha vazia do tamanho do cabeçalho
            row = [''] * len(header_row)

            # Buscamos TODAS as respostas desse paciente para os questionários em questão
            respostas_do_paciente = Resposta.objects.filter(
                session_key=sessao,
                pergunta__questionario__id__in=ids_questionarios
            ).select_related('pergunta')

            if not respostas_do_paciente.exists():
                continue

            # Preencher dados fixos (Pega da primeira resposta encontrada)
            primeira_resp = respostas_do_paciente.first()
            row[0] = sessao
            row[1] = primeira_resp.data_resposta.strftime('%d/%m/%Y %H:%M')

            # Tenta achar o perfil do paciente
            perfil_nome = '-'
            sessao_obj = SessaoPaciente.objects.filter(session_key=sessao).first()
            if sessao_obj and sessao_obj.narrativa_perfil:
                perfil_nome = sessao_obj.narrativa_perfil.titulo
            row[2] = perfil_nome

            # Preencher as respostas nas colunas certas
            for resp in respostas_do_paciente:
                # Descobre em qual coluna essa pergunta deve ficar
                indice_coluna = mapa_pergunta_coluna.get(resp.pergunta.id)

                if indice_coluna is not None:
                    # Se for múltipla escolha, pode ter vírgulas, mantemos como texto
                    row[indice_coluna] = resp.texto_resposta

            # Adiciona a linha completa ao Excel
            dataset.append(row)

        # 5. Enviar para Download
        response = HttpResponse(dataset.xlsx,
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="relatorio_pacientes_colunas.xlsx"'
        return response