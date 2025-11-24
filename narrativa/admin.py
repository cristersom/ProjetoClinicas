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


# --- ADMINS SIMPLES ---
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


# --- FILTROS ---
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


# --- INLINES ---
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


# --- REGISTROS PRINCIPAIS ---
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
            path('<path:object_id>/relatorio_percurso/', self.admin_site.admin_view(self.relatorio_percurso_view),
                 name='narrativa_narrativa_percurso')]
        return custom_urls + urls

    def links_relatorios(self, obj):
        return format_html('<a class="button" href="{}">Relatório de Percurso</a>',
                           reverse('admin:narrativa_narrativa_percurso', args=[obj.pk]))

    links_relatorios.short_description = 'Relatórios'

    def relatorio_percurso_view(self, request, object_id, *args, **kwargs):
        narrativa = self.get_object(request, object_id)
        # Lógica simplificada para o exemplo
        context = {**self.admin_site.each_context(request), 'narrativa': narrativa,
                   'title': f"Percurso: {narrativa.titulo}"}
        return render(request, 'admin/relatorio_narrativa_percurso.html', context)


@admin.register(Questionario)
class QuestionarioAdmin(nested_admin.NestedModelAdmin):
    list_display = ('titulo', 'cena_associada', 'links_relatorios')
    inlines = [PerguntaInline]

    class Media: css = {'all': ('css/admin_custom.css',)}

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

    def resumo_agregado_view(self, request, object_id, *args, **kwargs):
        # ... (Mantido lógica de relatório agregado)
        return render(request, 'admin/relatorio_questionario_agregado.html', {**self.admin_site.each_context(request)})

    def relatorio_detalhado_view(self, request, object_id, *args, **kwargs):
        return render(request, 'admin/relatorio_questionario_detalhe.html', {**self.admin_site.each_context(request)})


@admin.register(SessaoPaciente)
class SessaoPacienteAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'narrativa_perfil', 'data_criacao')
    list_filter = ('narrativa_perfil',)


class RespostaResource(resources.ModelResource):
    class Meta:
        model = Resposta


# --- ADMIN DE RESPOSTAS COM AÇÃO DE PIVOT ---
@admin.register(Resposta)
class RespostaAdmin(ImportExportModelAdmin):
    resource_class = RespostaResource
    list_display = ('id', 'get_questionario', 'pergunta', 'session_key', 'texto_resposta', 'data_resposta')
    list_filter = (NarrativaPerfilFilter, 'pergunta__questionario', 'data_resposta')

    # AQUI ESTÁ A MÁGICA: Adicionamos a ação no menu dropdown
    actions = ['exportar_tabela_pacientes']

    def get_questionario(self, obj):
        return obj.pergunta.questionario.titulo

    get_questionario.short_description = 'Questionário'

    @admin.action(description='>> EXPORTAR TABELA EXCEL (1 Linha por Paciente) <<')
    def exportar_tabela_pacientes(self, request, queryset):
        # 1. Identifica quais questionários estão envolvidos na seleção
        # Isso define quais COLUNAS teremos
        questionarios_ids = queryset.values_list('pergunta__questionario', flat=True).distinct()
        perguntas = Pergunta.objects.filter(questionario__in=questionarios_ids).order_by('questionario__titulo', 'id')

        # 2. Identifica quais pacientes (sessões) estão na seleção
        sessoes_ids = queryset.values_list('session_key', flat=True).distinct()

        # 3. Prepara o Excel
        dataset = Dataset()

        # Cabeçalho
        headers = ['ID Sessão', 'Data', 'Perfil']
        perguntas_map = {}  # Mapa para saber em qual coluna colocar a resposta

        for i, p in enumerate(perguntas):
            # Cria coluna: "Nome do Questionário - Pergunta"
            col_name = f"{p.questionario.titulo} - {p.texto_pergunta}"
            headers.append(col_name)
            perguntas_map[p.id] = i + 3  # +3 offset (ID, Data, Perfil)

        dataset.headers = headers

        # 4. Preenche as linhas (Uma por Paciente)
        for sessao in sessoes_ids:
            # Busca TODAS as respostas desse paciente para os questionários selecionados
            # (Mesmo as que não foram marcadas no checkbox, para a linha ficar completa)
            respostas_paciente = Resposta.objects.filter(
                session_key=sessao,
                pergunta__questionario__in=questionarios_ids
            )

            if not respostas_paciente.exists(): continue

            # Dados fixos
            ultima_resp = respostas_paciente.latest('data_resposta')
            data_str = ultima_resp.data_resposta.strftime('%d/%m/%Y %H:%M')

            # Tenta pegar o perfil
            perfil_nome = '-'
            sessao_obj = SessaoPaciente.objects.filter(session_key=sessao).first()
            if sessao_obj and sessao_obj.narrativa_perfil:
                perfil_nome = sessao_obj.narrativa_perfil.titulo

            # Cria linha vazia
            row = [''] * len(headers)
            row[0] = sessao
            row[1] = data_str
            row[2] = perfil_nome

            # Preenche as colunas
            for resp in respostas_paciente:
                col_index = perguntas_map.get(resp.pergunta.id)
                if col_index is not None:
                    row[col_index] = resp.texto_resposta

            dataset.append(row)

        response = HttpResponse(dataset.xlsx,
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="respostas_pacientes_tabela.xlsx"'
        return response


admin.site.register(Usuario, UserAdmin)