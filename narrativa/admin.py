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

# Imports necessários para os relatórios customizados
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

# Importar o formulário customizado
from .forms import PerguntaAdminForm


# --- ADICIONADO NOVO ADMIN PARA CATEGORIA ---
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('titulo',)
    search_fields = ('titulo',)


# --- ADMIN ADICIONADO PARA O LOGO ---
@admin.register(ConfiguracaoClinica)
class ConfiguracaoClinicaAdmin(admin.ModelAdmin):
    list_display = ('logo',)

    def has_add_permission(self, request):
        # Impede a criação de novos objetos se um já existir (pk=1)
        return not ConfiguracaoClinica.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Impede a exclusão do objeto de configuração
        return False


# --- FIM DA ADIÇÃO ---


# --- Filtro de Perfil (usado em RespostaAdmin) ---
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


# --- Classes Inline ---
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
    form = PerguntaAdminForm  # Usa o formulário customizado
    fk_name = 'questionario'
    extra = 1
    inlines = [OpcaoRespostaInline]


# --- Registros dos Modelos no Admin ---
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

    links_relatorios.short_description = 'Relatório de Percurso'

    def relatorio_percurso_view(self, request, object_id, *args, **kwargs):
        """
        View que mostra dados AGREGADOS do percurso de cenas visitadas
        e permite EXPORTAR em múltiplos formatos (XLSX, CSV, JSON).
        """
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
            '<a class="button" href="{}">Ver Detalhado (por Paciente)</a>&nbsp;'
            '<a class="button" href="{}">Ver Resumo (Agregado)</a>',
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

        respostas_base = Resposta.objects.filter(pergunta__questionario=questionario)
        dados_comparativos = {}

        export_dataset = Dataset()
        export_dataset.headers = ['Pergunta', 'Tipo de Pergunta', 'Perfil do Paciente', 'Opção/Resposta', 'Contagem']

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
                    for resposta_texto in dados_grafico_processado:
                        export_dataset.append(
                            [pergunta.texto_pergunta, pergunta.tipo_resposta, perfil_info['titulo'], resposta_texto, 1])
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
                    for label, count in dados_grafico_processado.items():
                        export_dataset.append(
                            [pergunta.texto_pergunta, pergunta.tipo_resposta, perfil_info['titulo'], label, count])

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

        export_format = request.GET.get('export')
        if export_format in ['csv', 'xlsx', 'json']:
            if export_format == 'xlsx':
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                file_data = export_dataset.xlsx
            elif export_format == 'json':
                content_type = 'application/json'
                file_data = export_dataset.json
            else:
                content_type = 'text/csv'
                file_data = export_dataset.csv

            response = HttpResponse(file_data, content_type=content_type)
            response['Content-Disposition'] = f'resumo_questionario_{questionario.id}.{export_format}'
            return response

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


# --- Define RespostaResource ANTES de RespostaAdmin ---
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


# ----------------------------------------------------

@admin.register(Resposta)
class RespostaAdmin(ImportExportModelAdmin):
    resource_class = RespostaResource
    list_display = (
        'id', 'questionario_associado', 'pergunta', 'session_key_abreviada', 'texto_resposta', 'data_resposta')
    list_filter = (NarrativaPerfilFilter, 'pergunta__questionario', 'data_resposta',)
    search_fields = ('texto_resposta', 'session_key')
    ordering = ('session_key', 'pergunta__questionario', 'pergunta__id')

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
        todos_os_perfis = Narrativa.objects.all()
        todos_os_questionarios = Questionario.objects.all()
        perfis_selecionados_ids = request.GET.getlist('narrativa_perfil_id')
        questionarios_selecionados_ids = request.GET.getlist('questionario_id')
        respostas_base = Resposta.objects.all()

        if questionarios_selecionados_ids and 'all' not in questionarios_selecionados_ids:
            respostas_base = respostas_base.filter(pergunta__questionario_id__in=questionarios_selecionados_ids)
        else:
            questionarios_selecionados_ids = ['all']

        perfis_a_processar = []
        if not perfis_selecionados_ids or 'all' in perfis_selecionados_ids:
            perfis_a_processar.append({'id': 'all', 'titulo': 'Todos os Perfis (Agregado)'})
            perfis_selecionados_ids = ['all']
        else:
            perfis_selecionados = list(Narrativa.objects.filter(id__in=perfis_selecionados_ids))
            for p in perfis_selecionados:
                perfis_a_processar.append({'id': p.id, 'titulo': p.titulo})

        if 'all' in questionarios_selecionados_ids:
            perguntas = Pergunta.objects.all().order_by('questionario__id', 'id')
        else:
            perguntas = Pergunta.objects.filter(questionario_id__in=questionarios_selecionados_ids).order_by(
                'questionario__id', 'id')

        dados_comparativos = {}

        export_dataset = Dataset()
        export_dataset.headers = ['Questionário', 'Pergunta', 'Tipo de Pergunta', 'Perfil do Paciente',
                                  'Opção/Resposta', 'Contagem']

        for pergunta in perguntas:
            dados_comparativos[pergunta.id] = {
                'pergunta_texto': f"({pergunta.questionario.titulo}) - {pergunta.texto_pergunta}",
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
                    for resposta_texto in dados_grafico_processado:
                        export_dataset.append(
                            [pergunta.questionario.titulo, pergunta.texto_pergunta, pergunta.tipo_resposta,
                             perfil_info['titulo'], resposta_texto, 1])
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

                    for label, count in dados_grafico_processado.items():
                        export_dataset.append(
                            [pergunta.questionario.titulo, pergunta.texto_pergunta, pergunta.tipo_resposta,
                             perfil_info['titulo'], label, count])

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

        export_format = request.GET.get('export')
        if export_format in ['csv', 'xlsx', 'json']:
            if export_format == 'xlsx':
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                file_data = export_dataset.xlsx
            elif export_format == 'json':
                content_type = 'application/json'
                file_data = export_dataset.json
            else:
                content_type = 'text/csv'
                file_data = export_dataset.csv

            response = HttpResponse(file_data, content_type=content_type)
            response['Content-Disposition'] = f'resumo_global_respostas.{export_format}'
            return response

        context = {
            **self.admin_site.each_context(request),
            'title': "Relatório Global Comparativo de Respostas",
            'dados_comparativos': dados_comparativos,
            'todos_os_perfis': todos_os_perfis,
            'perfis_selecionados_ids': perfis_selecionados_ids,
            'todos_os_questionarios': todos_os_questionarios,
            'questionarios_selecionados_ids': questionarios_selecionados_ids,
        }
        return render(request, 'admin/relatorio_resumo_global.html', context)

    def questionario_associado(self, obj):
        return obj.pergunta.questionario.titulo

    questionario_associado.short_description = 'Questionário'

    def session_key_abreviada(self, obj):
        return obj.session_key[:8] + '...'

    session_key_abreviada.short_description = 'Sessão do Paciente'


# Registra o usuário customizado
admin.site.register(Usuario, UserAdmin)