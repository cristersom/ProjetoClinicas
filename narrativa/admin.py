from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
import nested_admin
from .models import (
    Narrativa, Cena, Escolha, Questionario, Pergunta, Usuario, Resposta,
    SessaoPaciente, OpcaoResposta, LogVisitaCena,
    Categoria, ConfiguracaoClinica
)
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields

# Imports para relatórios e exportação
from django.urls import path, reverse
from django.http import HttpResponse
from tablib import Dataset
from django.shortcuts import render
from django.utils.html import format_html
from collections import Counter
import json
from django.db.models import Count, Value
from django.db.models.functions import Coalesce
from .forms import PerguntaAdminForm


# --- 1. CONFIGURAÇÕES GERAIS ---

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


# --- 2. FILTROS ---

class NarrativaPerfilFilter(admin.SimpleListFilter):
    title = 'por Perfil (Narrativa)'
    parameter_name = 'narrativa_perfil'

    def lookups(self, request, model_admin):
        return [(narrativa.id, narrativa.titulo) for narrativa in Narrativa.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            sessoes = SessaoPaciente.objects.filter(narrativa_perfil_id=self.value())
            return queryset.filter(session_key__in=sessoes.values_list('session_key', flat=True))
        return queryset


# --- 3. INLINES (Para criação de Narrativas/Questionários) ---

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


# --- 4. ADMINS PRINCIPAIS ---

@admin.register(Cena)
class CenaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'narrativa')
    list_filter = ('narrativa',)
    inlines = [EscolhaInline]


@admin.register(Narrativa)
class NarrativaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'data_criacao', 'links_relatorios')
    list_filter = ('categoria',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/relatorio_percurso/', self.admin_site.admin_view(self.relatorio_percurso_view),
                 name='narrativa_narrativa_percurso')]
        return custom_urls + urls

    def links_relatorios(self, obj):
        return format_html('<a class="button" href="{}">Relatório de Percurso</a>',
                           reverse('admin:narrativa_narrativa_percurso', args=[obj.pk]))

    links_relatorios.short_description = 'Relatórios'

    def relatorio_percurso_view(self, request, object_id, *args, **kwargs):
        narrativa = self.get_object(request, object_id)
        # Lógica de relatório de percurso simplificada para evitar erros
        return render(request, 'admin/relatorio_narrativa_percurso.html', {
            **self.admin_site.each_context(request),
            'narrativa': narrativa,
            'title': f"Percurso: {narrativa.titulo}"
        })


@admin.register(Questionario)
class QuestionarioAdmin(nested_admin.NestedModelAdmin):
    list_display = ('titulo', 'cena_associada', 'links_relatorios')
    inlines = [PerguntaInline]

    class Media:
        css = {'all': ('css/admin_custom.css',)}

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/resumo/', self.admin_site.admin_view(self.resumo_agregado_view),
                 name='narrativa_questionario_resumo_agregado'),
            path('<path:object_id>/relatorio_detalhe/', self.admin_site.admin_view(self.relatorio_detalhado_view),
                 name='narrativa_questionario_relatorio_detalhe'),
        ]
        return custom_urls + urls

    def links_relatorios(self, obj):
        url_detalhe = reverse('admin:narrativa_questionario_relatorio_detalhe', args=[obj.pk])
        url_resumo = reverse('admin:narrativa_questionario_resumo_agregado', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">Ver Detalhado</a>&nbsp;<a class="button" href="{}">Ver Resumo</a>',
            url_detalhe, url_resumo)

    # VIEW DO RELATÓRIO AGREGADO (GRÁFICOS)
    def resumo_agregado_view(self, request, object_id, *args, **kwargs):
        questionario = self.get_object(request, object_id)
        todos_os_perfis = Narrativa.objects.all()

        # Dados base: Todas as respostas deste questionário
        respostas_base = Resposta.objects.filter(pergunta__questionario=questionario)

        dados_comparativos = {}

        # Itera sobre as perguntas para montar os dados
        for pergunta in questionario.perguntas.all():
            respostas_pergunta = respostas_base.filter(pergunta=pergunta)
            total_respostas = respostas_pergunta.count()

            dados_grafico = None
            respostas_texto = []

            if pergunta.tipo_resposta == "TEXTO":
                respostas_texto = list(respostas_pergunta.values_list('texto_resposta', flat=True))

            elif pergunta.tipo_resposta in ["UNICA_ESCOLHA", "ESCALA_5", "MULTIPLA_ESCOLHA"]:
                contador = Counter()
                if pergunta.tipo_resposta == "MULTIPLA_ESCOLHA":
                    for r in respostas_pergunta:
                        contador.update(r.texto_resposta.split(','))
                else:
                    contador.update(list(respostas_pergunta.values_list('texto_resposta', flat=True)))

                labels = list(contador.keys())
                data = list(contador.values())

                dados_grafico = {
                    'labels': json.dumps(labels),
                    'data': json.dumps(data),
                    'tipo_grafico': 'pie' if pergunta.tipo_resposta == "UNICA_ESCOLHA" else 'bar'
                }

            # Estrutura simplificada para não depender de filtro de perfil se não houver
            dados_comparativos[pergunta.id] = {
                'pergunta_texto': pergunta.texto_pergunta,
                'pergunta_tipo': pergunta.get_tipo_resposta_display,
                'pergunta_tipo_raw': pergunta.tipo_resposta,
                'dados_por_perfil': [{
                    'perfil_titulo': 'Geral (Todos)',
                    'total_respostas': total_respostas,
                    'dados_grafico': dados_grafico,
                    'respostas_texto': respostas_texto
                }]
            }

        context = {
            **self.admin_site.each_context(request),
            'title': f"Resumo: {questionario.titulo}",
            'questionario': questionario,
            'dados_comparativos': dados_comparativos,
            'todos_os_perfis': todos_os_perfis,
        }
        return render(request, 'admin/relatorio_questionario_agregado.html', context)

    # VIEW DO RELATÓRIO DETALHADO (LISTA)
    def relatorio_detalhado_view(self, request, object_id, *args, **kwargs):
        questionario = self.get_object(request, object_id)
        # Busca TODAS as respostas, ordenadas por sessão (paciente)
        respostas = Resposta.objects.filter(pergunta__questionario=questionario).order_by('session_key', 'pergunta__id')

        dados_do_relatorio = {}
        for r in respostas:
            if r.session_key not in dados_do_relatorio:
                dados_do_relatorio[r.session_key] = []
            dados_do_relatorio[r.session_key].append(r)

        context = {
            **self.admin_site.each_context(request),
            'title': f"Detalhado: {questionario.titulo}",
            'questionario': questionario,
            'dados_do_relatorio': dados_do_relatorio
        }
        return render(request, 'admin/relatorio_questionario_detalhe.html', context)


@admin.register(SessaoPaciente)
class SessaoPacienteAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'narrativa_perfil', 'data_criacao')
    list_filter = ('narrativa_perfil',)


# --- 5. EXPORTAÇÃO DE RESPOSTAS (PIVOT TABLE) ---

class RespostaResource(resources.ModelResource):
    class Meta:
        model = Resposta


@admin.register(Resposta)
class RespostaAdmin(ImportExportModelAdmin):
    resource_class = RespostaResource
    list_display = ('id', 'get_questionario', 'pergunta', 'session_key', 'texto_resposta', 'data_resposta')
    list_filter = (NarrativaPerfilFilter, 'pergunta__questionario', 'data_resposta')

    # AÇÃO CUSTOMIZADA PARA EXPORTAR LINHA POR PACIENTE
    actions = ['exportar_respostas_pivot']

    def get_questionario(self, obj):
        return obj.pergunta.questionario.titulo

    get_questionario.short_description = 'Questionário'

    @admin.action(description='📊 BAIXAR EXCEL FORMATADO (1 Linha por Paciente)')
    def exportar_respostas_pivot(self, request, queryset):
        # 1. Descobrir quais questionários estão na seleção
        ids_questionarios = queryset.values_list('pergunta__questionario', flat=True).distinct()

        # 2. Pegar TODAS as perguntas desses questionários para fazer o CABEÇALHO
        perguntas = Pergunta.objects.filter(questionario__in=ids_questionarios).order_by('questionario__titulo', 'id')

        # 3. Identificar todos os pacientes (sessões) envolvidos
        sessoes_ids = queryset.values_list('session_key', flat=True).distinct()

        # 4. Montar o Excel
        dataset = Dataset()

        # Cabeçalho Fixo + Perguntas Dinâmicas
        headers = ['ID Sessão', 'Data', 'Perfil']
        perguntas_map = {}  # ID da Pergunta -> Índice da Coluna

        for i, p in enumerate(perguntas):
            col_name = f"{p.texto_pergunta}"  # Texto da pergunta no cabeçalho
            headers.append(col_name)
            perguntas_map[p.id] = i + 3  # +3 por causa das colunas fixas

        dataset.headers = headers

        # Preencher Linhas
        for sessao in sessoes_ids:
            # Busca TODAS as respostas desse paciente para os questionários selecionados
            respostas_paciente = Resposta.objects.filter(
                session_key=sessao,
                pergunta__questionario__in=ids_questionarios
            )

            if not respostas_paciente.exists(): continue

            # Dados fixos
            ultima = respostas_paciente.latest('data_resposta')
            data_str = ultima.data_resposta.strftime('%d/%m/%Y %H:%M')

            # Tenta pegar o perfil da sessão
            perfil_nome = '-'
            sessao_obj = SessaoPaciente.objects.filter(session_key=sessao).first()
            if sessao_obj and sessao_obj.narrativa_perfil:
                perfil_nome = sessao_obj.narrativa_perfil.titulo

            # Cria a linha vazia
            row = [''] * len(headers)
            row[0] = sessao
            row[1] = data_str
            row[2] = perfil_nome

            # Preenche as colunas com as respostas
            for r in respostas_paciente:
                col_idx = perguntas_map.get(r.pergunta.id)
                if col_idx is not None:
                    row[col_idx] = r.texto_resposta

            dataset.append(row)

        response = HttpResponse(dataset.xlsx,
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="respostas_pacientes_pivot.xlsx"'
        return response


admin.site.register(Usuario, UserAdmin)