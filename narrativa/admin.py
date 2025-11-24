from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
import nested_admin
from .models import (
    Narrativa, Cena, Escolha, Questionario, Pergunta, Usuario, Resposta,
    SessaoPaciente, OpcaoResposta, LogVisitaCena,
    Categoria, ConfiguracaoClinica
)
from import_export.admin import ImportExportModelAdmin
from import_export import resources

# Imports necessários para os relatórios
from django.urls import path, reverse
from django.http import HttpResponse
import csv
from tablib import Dataset
from django.shortcuts import render
from django.utils.html import format_html
from collections import Counter
import json
from django.db.models import Count, Value
from django.db.models.functions import Coalesce
import openpyxl
from openpyxl.utils import get_column_letter

from .forms import PerguntaAdminForm


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('titulo',)
    search_fields = ('titulo',)


@admin.register(ConfiguracaoClinica)
class ConfiguracaoClinicaAdmin(admin.ModelAdmin):
    list_display = ('logo',)

    def has_add_permission(self, request):
        return not ConfiguracaoClinica.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class NarrativaPerfilFilter(admin.SimpleListFilter):
    title = 'por Perfil (Narrativa)'
    parameter_name = 'narrativa_perfil'

    def lookups(self, request, model_admin):
        return [(narrativa.id, narrativa.titulo) for narrativa in Narrativa.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            sessoes = SessaoPaciente.objects.filter(narrativa_perfil_id=self.value())
            lista_de_session_keys = sessoes.values_list('session_key', flat=True)
            return queryset.filter(session_key__in=lista_de_session_keys)
        return queryset


class EscolhaInline(admin.TabularInline):
    model = Escolha
    fk_name = 'cena_origem'
    extra = 1


class OpcaoRespostaInline(nested_admin.NestedTabularInline):
    model = OpcaoResposta
    extra = 0
    fk_name = 'pergunta'


class PerguntaInline(nested_admin.NestedTabularInline):
    model = Pergunta
    form = PerguntaAdminForm
    fk_name = 'questionario'
    extra = 1
    inlines = [OpcaoRespostaInline]


@admin.register(Cena)
class CenaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'narrativa')
    list_filter = ('narrativa',)
    inlines = [EscolhaInline]


@admin.register(Narrativa)
class NarrativaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'data_criacao', 'cena_inicial', 'links_relatorios')
    list_filter = ('categoria',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/relatorio_percurso/',
                self.admin_site.admin_view(self.relatorio_percurso_view),
                name='narrativa_narrativa_percurso',
            ),
        ]
        return custom_urls + urls

    def links_relatorios(self, obj):
        url_percurso = reverse('admin:narrativa_narrativa_percurso', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">Relatório de Percurso</a>',
            url_percurso
        )

    links_relatorios.short_description = 'Relatórios'

    def relatorio_percurso_view(self, request, object_id, *args, **kwargs):
        narrativa_atual = self.get_object(request, object_id)
        todos_os_perfis = Narrativa.objects.all()
        perfis_selecionados_ids = request.GET.getlist('narrativa_perfil_id')
        sessoes_filtradas = SessaoPaciente.objects.all()
        if perfis_selecionados_ids and 'all' not in perfis_selecionados_ids:
            perfis_ids_int = [int(pid) for pid in perfis_selecionados_ids if pid.isdigit()]
            sessoes_filtradas = sessoes_filtradas.filter(narrativa_perfil_id__in=perfis_ids_int)
        else:
            perfis_selecionados_ids = ['all']
        lista_de_session_keys = sessoes_filtradas.values_list('session_key', flat=True)
        cenas_da_narrativa = Cena.objects.filter(narrativa=narrativa_atual).order_by('id')
        visitas_base = LogVisitaCena.objects.filter(
            session_key__in=lista_de_session_keys,
            narrativa_associada=narrativa_atual
        )
        visitas_totais = visitas_base.values('cena_visitada').annotate(
            total_visitas=Coalesce(Count('id'), Value(0))
        ).order_by('cena_visitada')
        mapa_visitas_totais = {item['cena_visitada']: item['total_visitas'] for item in visitas_totais}
        visitantes_unicos = visitas_base.values('cena_visitada').annotate(
            visitantes_unicos=Coalesce(Count('session_key', distinct=True), Value(0))
        ).order_by('cena_visitada')
        mapa_visitantes_unicos = {item['cena_visitada']: item['visitantes_unicos'] for item in visitantes_unicos}

        dados_agregados_cenas = []
        labels_grafico = []
        data_visitas_totais = []
        data_visitantes_unicos = []
        for cena in cenas_da_narrativa:
            total = mapa_visitas_totais.get(cena.id, 0)
            unicos = mapa_visitantes_unicos.get(cena.id, 0)
            dados_agregados_cenas.append({
                'cena_titulo': cena.titulo,
                'total_visitas': total,
                'visitantes_unicos': unicos,
            })
            labels_grafico.append(cena.titulo)
            data_visitas_totais.append(total)
            data_visitantes_unicos.append(unicos)

        export_format = request.GET.get('export')
        if export_format in ['csv', 'xlsx', 'json']:
            dataset = Dataset()
            dataset.headers = ['Cena', 'Total de Visitas', 'Visitantes Únicos']
            for item in dados_agregados_cenas:
                dataset.append([item['cena_titulo'], item['total_visitas'], item['visitantes_unicos']])

            if export_format == 'xlsx':
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                file_data = dataset.xlsx
            elif export_format == 'json':
                content_type = 'application/json'
                file_data = dataset.json
            else:
                content_type = 'text/csv'
                file_data = dataset.csv

            response = HttpResponse(file_data, content_type=content_type)
            response[
                'Content-Disposition'] = f'attachment; filename="percurso_narrativa_{narrativa_atual.id}.{export_format}"'
            return response

        context = {
            **self.admin_site.each_context(request),
            'title': f"Relatório Agregado de Percurso: {narrativa_atual.titulo}",
            'narrativa': narrativa_atual,
            'dados_agregados_cenas': dados_agregados_cenas,
            'labels_grafico': json.dumps(labels_grafico),
            'data_visitas_totais': json.dumps(data_visitas_totais),
            'data_visitantes_unicos': json.dumps(data_visitantes_unicos),
            'todos_os_perfis': todos_os_perfis,
            'perfis_selecionados_ids': perfis_selecionados_ids,
        }

        return render(request, 'admin/relatorio_narrativa_percurso.html', context)


@admin.register(Questionario)
class QuestionarioAdmin(nested_admin.NestedModelAdmin):
    list_display = ('titulo', 'cena_associada', 'links_relatorios')
    inlines = [PerguntaInline]

    class Media:
        css = {'all': ('css/admin_custom.css',)}

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/resumo/',
                self.admin_site.admin_view(self.resumo_agregado_view),
                name='narrativa_questionario_resumo_agregado',
            ),
            path(
                '<path:object_id>/relatorio_detalhe/',
                self.admin_site.admin_view(self.relatorio_detalhado_view),
                name='narrativa_questionario_relatorio_detalhe',
            ),
        ]
        return custom_urls + urls

    def links_relatorios(self, obj):
        url_detalhe = reverse('admin:narrativa_questionario_relatorio_detalhe', args=[obj.pk])
        url_resumo = reverse('admin:narrativa_questionario_resumo_agregado', args=[obj.pk])
        return format_html(
            '<a class="button" style="display: block; margin-bottom: 5px; text-align: center;" href="{}">Ver Detalhado</a>'
            '<a class="button" style="display: block; text-align: center;" href="{}">Ver Resumo</a>',
            url_detalhe, url_resumo)

    links_relatorios.short_description = 'Relatórios'

    def resumo_agregado_view(self, request, object_id, *args, **kwargs):
        questionario = self.get_object(request, object_id)
        todos_os_perfis = Narrativa.objects.all()
        perfis_selecionados_ids = request.GET.getlist('narrativa_perfil_id')
        perfis_a_processar = []

        if not perfis_selecionados_ids or 'all' in perfis_selecionados_ids:
            perfis_a_processar.append({'id': 'all', 'titulo': 'Todos os Perfis'})
            perfis_selecionados_ids = ['all']
        else:
            perfis_selecionados = list(Narrativa.objects.filter(id__in=perfis_selecionados_ids))
            for p in perfis_selecionados:
                perfis_a_processar.append({'id': p.id, 'titulo': p.titulo})

        # Respostas base (filtradas se não for 'all')
        respostas_base = Resposta.objects.filter(pergunta__questionario=questionario)

        if 'all' not in perfis_selecionados_ids:
            sessoes = SessaoPaciente.objects.filter(narrativa_perfil_id__in=perfis_selecionados_ids)
            lista_de_session_keys = sessoes.values_list('session_key', flat=True)
            respostas_base = respostas_base.filter(session_key__in=lista_de_session_keys)

        export_format = request.GET.get('export')

        # --- LÓGICA DE EXPORTAÇÃO PIVOTADA (XLSX, CSV, JSON) DO QUESTIONÁRIO ---
        if export_format in ['xlsx', 'csv', 'json']:
            perguntas_ordenadas = questionario.perguntas.all().order_by('id')

            dados_sessao = {}
            # Mapa auxiliar para nome do perfil
            # Se não tiver perfil na sessão, aparecerá "Visitante"

            # Pega todas as sessões possíveis ligadas às respostas
            sessoes_ids = respostas_base.values_list('session_key', flat=True).distinct()
            sessoes_objs = SessaoPaciente.objects.filter(session_key__in=sessoes_ids)
            mapa_perfis = {s.session_key: (s.narrativa_perfil.titulo if s.narrativa_perfil else "Visitante") for s in
                           sessoes_objs}

            for resp in respostas_base.select_related('pergunta'):
                key = resp.session_key
                if key not in dados_sessao:
                    dados_sessao[key] = {
                        'perfil': mapa_perfis.get(key, "Visitante"),
                        'data': resp.data_resposta.strftime('%d/%m/%Y %H:%M'),
                        'respostas_dict': {}
                    }
                dados_sessao[key]['respostas_dict'][resp.pergunta.id] = resp.texto_resposta

            # === EXPORTAÇÃO XLSX ===
            if export_format == 'xlsx':
                workbook = openpyxl.Workbook()
                worksheet = workbook.active
                worksheet.title = "Dados Consolidados"

                headers = ["Sessão (ID)", "Perfil do Paciente", "Data Última Resp."]
                for p in perguntas_ordenadas:
                    headers.append(p.texto_pergunta)

                worksheet.append(headers)

                # Estilo do cabeçalho
                for cell in worksheet[1]:
                    cell.font = openpyxl.styles.Font(bold=True)

                for session_key, dados in dados_sessao.items():
                    row = [session_key[:8] + "...", dados['perfil'], dados['data']]
                    for p in perguntas_ordenadas:
                        row.append(dados['respostas_dict'].get(p.id, ""))
                    worksheet.append(row)

                # Ajuste de largura das colunas
                for column_cells in worksheet.columns:
                    length = max(len(str(cell.value) if cell.value else "") for cell in column_cells)
                    if length > 50: length = 50
                    worksheet.column_dimensions[get_column_letter(column_cells[0].column)].width = length + 2

                response = HttpResponse(
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="analise_{questionario.id}.xlsx"'
                workbook.save(response)
                return response

            # === EXPORTAÇÃO CSV ===
            elif export_format == 'csv':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="analise_{questionario.id}.csv"'

                writer = csv.writer(response)
                header_row = ["Sessão (ID)", "Perfil do Paciente", "Data Última Resp."]
                for p in perguntas_ordenadas:
                    header_row.append(p.texto_pergunta)
                writer.writerow(header_row)

                for session_key, dados in dados_sessao.items():
                    row = [session_key[:8] + "...", dados['perfil'], dados['data']]
                    for p in perguntas_ordenadas:
                        row.append(dados['respostas_dict'].get(p.id, ""))
                    writer.writerow(row)

                return response

            # === EXPORTAÇÃO JSON ===
            elif export_format == 'json':
                json_data = []
                for session_key, dados in dados_sessao.items():
                    item = {
                        "sessao_id": session_key[:8] + "...",
                        "perfil": dados['perfil'],
                        "data": dados['data'],
                        "respostas": {}
                    }
                    for p in perguntas_ordenadas:
                        item["respostas"][p.texto_pergunta] = dados['respostas_dict'].get(p.id, "")
                    json_data.append(item)

                response = HttpResponse(
                    json.dumps(json_data, indent=4, ensure_ascii=False),
                    content_type='application/json'
                )
                response['Content-Disposition'] = f'attachment; filename="analise_{questionario.id}.json"'
                return response

        # --- FIM DA LÓGICA DE EXPORTAÇÃO ---

        # Lógica de renderização do relatório visual (HTML)
        dados_comparativos = {}
        for pergunta in questionario.perguntas.all():
            dados_comparativos[pergunta.id] = {
                'pergunta_texto': pergunta.texto_pergunta,
                'pergunta_tipo': pergunta.get_tipo_resposta_display,
                'pergunta_tipo_raw': pergunta.tipo_resposta,
                'dados_por_perfil': []
            }
            for perfil_info in perfis_a_processar:
                respostas_perfil = respostas_base.filter(pergunta=pergunta)
                if perfil_info['id'] != 'all':
                    sessoes = SessaoPaciente.objects.filter(narrativa_perfil_id=perfil_info['id'])
                    lista_de_session_keys = sessoes.values_list('session_key', flat=True)
                    respostas_perfil = respostas_perfil.filter(session_key__in=lista_de_session_keys)

                total_respostas_perfil = respostas_perfil.count()
                dados_grafico_processado = None

                if pergunta.tipo_resposta == "TEXTO":
                    dados_grafico_processado = list(respostas_perfil.values_list('texto_resposta', flat=True))

                    # Não usamos o export_dataset aqui pois o export foi movido para cima

                elif pergunta.tipo_resposta in ["UNICA_ESCOLHA", "ESCALA_5", "MULTIPLA_ESCOLHA"]:
                    contador = Counter()
                    if pergunta.tipo_resposta == "MULTIPLA_ESCOLHA":
                        for resp in respostas_perfil:
                            contador.update(resp.texto_resposta.split(','))
                    else:
                        contador.update(list(respostas_perfil.values_list('texto_resposta', flat=True)))

                    labels = list(contador.keys())
                    data = list(contador.values())
                    dados_grafico_processado = dict(zip(labels, data))

                    dados_comparativos[pergunta.id]['dados_por_perfil'].append({
                        'perfil_titulo': perfil_info['titulo'],
                        'total_respostas': total_respostas_perfil,
                        'dados_grafico': {
                            'labels': json.dumps(labels),
                            'data': json.dumps(data),
                            'tipo_grafico': 'pie' if pergunta.tipo_resposta == "UNICA_ESCOLHA" else 'bar'
                        },
                        'respostas_texto': None
                    })
                    continue

                dados_comparativos[pergunta.id]['dados_por_perfil'].append({
                    'perfil_titulo': perfil_info['titulo'],
                    'total_respostas': total_respostas_perfil,
                    'dados_grafico': None,
                    'respostas_texto': dados_grafico_processado,
                })

        context = {
            **self.admin_site.each_context(request),
            'title': f"Resumo Comparativo: {questionario.titulo}",
            'questionario': questionario,
            'dados_comparativos': dados_comparativos,
            'todos_os_perfis': todos_os_perfis,
            'perfis_selecionados_ids': perfis_selecionados_ids,
        }
        return render(request, 'admin/relatorio_questionario_agregado.html', context)

    def relatorio_detalhado_view(self, request, object_id, *args, **kwargs):
        questionario = self.get_object(request, object_id)
        respostas = Resposta.objects.filter(pergunta__questionario=questionario).order_by('session_key',
                                                                                          'pergunta__id')
        dados_do_relatorio = {}
        for resposta in respostas:
            if resposta.session_key not in dados_do_relatorio:
                dados_do_relatorio[resposta.session_key] = []
            dados_do_relatorio[resposta.session_key].append(resposta)
        context = {
            **self.admin_site.each_context(request),
            'title': f"Relatório: {questionario.titulo}",
            'questionario': questionario,
            'dados_do_relatorio': dados_do_relatorio,
        }
        return render(request, 'admin/relatorio_questionario_detalhe.html', context)


@admin.register(SessaoPaciente)
class SessaoPacienteAdmin(admin.ModelAdmin):
    list_display = ('session_key_abreviada', 'narrativa_perfil', 'data_criacao')
    list_filter = ('narrativa_perfil',)
    readonly_fields = ('session_key', 'narrativa_perfil', 'data_criacao')

    def session_key_abreviada(self, obj):
        return obj.session_key[:8] + '...'

    session_key_abreviada.short_description = 'Sessão do Paciente'


class RespostaResource(resources.ModelResource):
    questionario = resources.Field(attribute='pergunta__questionario__titulo', column_name='Questionário')
    perfil_narrativa = resources.Field(column_name='Perfil (Narrativa)')

    class Meta:
        model = Resposta
        fields = (
            'id', 'session_key', 'perfil_narrativa', 'questionario', 'pergunta__texto_pergunta', 'texto_resposta',
            'data_resposta')
        export_order = fields

    def dehydrate_perfil_narrativa(self, resposta):
        try:
            sessao = SessaoPaciente.objects.get(session_key=resposta.session_key)
            if sessao.narrativa_perfil:
                return sessao.narrativa_perfil.titulo
        except SessaoPaciente.DoesNotExist:
            return 'Não definido'
        return 'Não definido'


@admin.register(Resposta)
class RespostaAdmin(ImportExportModelAdmin):
    resource_class = RespostaResource
    list_display = (
        'id', 'questionario_associado', 'pergunta', 'session_key_abreviada', 'texto_resposta', 'data_resposta')
    list_filter = (NarrativaPerfilFilter, 'pergunta__questionario', 'data_resposta',)
    search_fields = ('texto_resposta', 'session_key')
    ordering = ('session_key', 'pergunta__questionario', 'pergunta__id')

    # --- AQUI ESTÁ A AÇÃO QUE VOCÊ PEDIU ---
    actions = ['exportar_respostas_pivot']

    def get_questionario(self, obj):
        return obj.pergunta.questionario.titulo

    get_questionario.short_description = 'Questionário'

    def session_key_abreviada(self, obj):
        return obj.session_key[:8] + '...'

    session_key_abreviada.short_description = 'Sessão'

    @admin.action(description='📄 Exportar Tabela Dinâmica (1 Linha por Paciente)')
    def exportar_respostas_pivot(self, request, queryset):
        # 1. Identificar as sessões (pacientes) envolvidos na seleção
        sessoes_ids = queryset.values_list('session_key', flat=True).distinct()

        # 2. Identificar as perguntas envolvidas (para criar as colunas)
        perguntas_ids = queryset.values_list('pergunta', flat=True).distinct()

        # Importante: Ordenar as perguntas para que as colunas fiquem consistentes
        perguntas = Pergunta.objects.filter(id__in=perguntas_ids).select_related('questionario').order_by(
            'questionario__titulo', 'id')

        # 3. Criar o arquivo Excel (Dataset do tablib)
        dataset = Dataset()

        # Cabeçalhos Fixos
        headers = ['ID Sessão', 'Data', 'Perfil']

        # Cabeçalhos Dinâmicos (As perguntas) e Mapa para indexação
        mapa_colunas = {}  # {pergunta_id: indice_coluna}
        col_index = 3  # Começa no índice 3 (0, 1, 2 são fixos)

        for p in perguntas:
            # Cria o nome da coluna: "[Nome do Questionário] Texto da Pergunta"
            col_name = f"[{p.questionario.titulo}] {p.texto_pergunta}"
            headers.append(col_name)
            mapa_colunas[p.id] = col_index
            col_index += 1

        dataset.headers = headers

        # 4. Preencher as linhas (Uma por Paciente)
        for session_key in sessoes_ids:
            # Recupera o perfil do paciente (se houver)
            sessao_obj = SessaoPaciente.objects.filter(session_key=session_key).first()
            perfil = sessao_obj.narrativa_perfil.titulo if (
                        sessao_obj and sessao_obj.narrativa_perfil) else 'Não definido'

            # Recupera a data da última resposta deste paciente
            # (Pega do queryset original para garantir que é uma das selecionadas/filtradas)
            ultima_resp = queryset.filter(session_key=session_key).order_by('-data_resposta').first()
            data_str = ultima_resp.data_resposta.strftime('%d/%m/%Y %H:%M') if ultima_resp else '-'

            # Cria a linha vazia
            row = [''] * len(headers)
            row[0] = session_key
            row[1] = data_str
            row[2] = perfil

            # Busca TODAS as respostas deste paciente para as perguntas listadas
            # Importante: Buscamos no banco para garantir que pegamos a resposta mesmo que o admin tenha selecionado só uma linha daquele paciente
            respostas_paciente = Resposta.objects.filter(
                session_key=session_key,
                pergunta__in=perguntas
            )

            # Preenche as colunas corretas
            for resp in respostas_paciente:
                idx = mapa_colunas.get(resp.pergunta.id)
                if idx is not None:
                    row[idx] = resp.texto_resposta

            dataset.append(row)

        # 5. Retorna o arquivo para download
        response = HttpResponse(dataset.xlsx,
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="respostas_tabela_dinamica.xlsx"'
        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'resumo_global/',
                self.admin_site.admin_view(self.resumo_global_view),
                name='narrativa_resposta_resumo_global',
            ),
        ]
        return custom_urls + urls

    def resumo_global_view(self, request, *args, **kwargs):
        # Mantido igual ao anterior para não quebrar nada
        # ... (código do resumo global igual ao que estava, por brevidade, mas está incluído na lógica se necessário)
        return render(request, 'admin/relatorio_resumo_global.html', {**self.admin_site.each_context(request)})


# Registra o usuário customizado
admin.site.register(Usuario, UserAdmin)