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


# --- 3. INLINES ---

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
        # ... (Lógica de percurso mantida simplificada)
        return render(request, 'admin/relatorio_narrativa_percurso.html', {
            **self.admin_site.each_context(request),
            'narrativa': narrativa,
            'title': f"Percurso: {narrativa.titulo}",
            # Passando listas vazias para não quebrar se não houver dados ainda
            'dados_agregados_cenas': [], 'labels_grafico': '[]', 'data_visitas_totais': '[]',
            'data_visitantes_unicos': '[]'
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

    def resumo_agregado_view(self, request, object_id, *args, **kwargs):
        questionario = self.get_object(request, object_id)
        # Lógica simplificada para garantir funcionamento
        respostas = Resposta.objects.filter(pergunta__questionario=questionario)

        dados_comparativos = {}
        for pergunta in questionario.perguntas.all():
            # Agrega respostas
            resps = respostas.filter(pergunta=pergunta)
            total = resps.count()

            dados_grafico = None
            respostas_texto = []

            if pergunta.tipo_resposta == 'TEXTO':
                respostas_texto = [r.texto_resposta for r in resps]
            elif total > 0:
                # Contagem simples para gráficos
                cnt = Counter([r.texto_resposta for r in resps])
                dados_grafico = {
                    'labels': json.dumps(list(cnt.keys())),
                    'data': json.dumps(list(cnt.values())),
                    'tipo_grafico': 'bar'
                }

            dados_comparativos[pergunta.id] = {
                'pergunta_texto': pergunta.texto_pergunta,
                'pergunta_tipo': pergunta.get_tipo_resposta_display,
                'pergunta_tipo_raw': pergunta.tipo_resposta,
                'dados_por_perfil': [{
                    'perfil_titulo': 'Geral (Todas as Respostas)',
                    'total_respostas': total,
                    'dados_grafico': dados_grafico,
                    'respostas_texto': respostas_texto
                }]
            }

        return render(request, 'admin/relatorio_questionario_agregado.html', {
            **self.admin_site.each_context(request),
            'questionario': questionario,
            'dados_comparativos': dados_comparativos
        })

    def relatorio_detalhado_view(self, request, object_id, *args, **kwargs):
        questionario = self.get_object(request, object_id)
        respostas = Resposta.objects.filter(pergunta__questionario=questionario).order_by('-data_resposta')

        dados_do_relatorio = {}
        for r in respostas:
            if r.session_key not in dados_do_relatorio:
                dados_do_relatorio[r.session_key] = []
            dados_do_relatorio[r.session_key].append(r)

        return render(request, 'admin/relatorio_questionario_detalhe.html', {
            **self.admin_site.each_context(request),
            'questionario': questionario,
            'dados_do_relatorio': dados_do_relatorio
        })


@admin.register(SessaoPaciente)
class SessaoPacienteAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'narrativa_perfil', 'data_criacao')
    list_filter = ('narrativa_perfil',)


# --- 5. EXPORTAÇÃO DE RESPOSTAS (FORMATADA/PIVOT) ---
# Removido ImportExportModelAdmin para evitar o botão de exportação padrão confuso.

@admin.register(Resposta)
class RespostaAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_questionario', 'pergunta', 'session_key_short', 'texto_resposta', 'data_resposta')
    list_filter = ('pergunta__questionario', 'data_resposta')
    search_fields = ('texto_resposta', 'session_key')

    # AQUI: Ação personalizada no menu dropdown
    actions = ['exportar_tabela_formatada']

    def get_questionario(self, obj):
        return obj.pergunta.questionario.titulo

    get_questionario.short_description = 'Questionário'

    def session_key_short(self, obj):
        return obj.session_key[:8] + '...'

    session_key_short.short_description = 'Sessão'

    @admin.action(description='📥 BAIXAR EXCEL (1 Linha por Paciente - Formatado)')
    def exportar_tabela_formatada(self, request, queryset):
        """
        Gera um Excel onde cada linha é um paciente e cada coluna é uma pergunta.
        """
        # 1. Identifica questionários e perguntas
        questionarios_ids = queryset.values_list('pergunta__questionario', flat=True).distinct()
        perguntas = Pergunta.objects.filter(questionario__in=questionarios_ids).order_by('questionario__titulo', 'id')

        # 2. Identifica sessões (pacientes)
        sessoes_ids = queryset.values_list('session_key', flat=True).distinct()

        # 3. Cria o Excel
        dataset = Dataset()

        # Cabeçalho
        headers = ['ID Sessão', 'Data', 'Perfil']
        perguntas_map = {}  # ID Pergunta -> Índice Coluna

        col_idx = 3
        for p in perguntas:
            # O texto da pergunta será o título da coluna
            headers.append(f"{p.texto_pergunta}")
            perguntas_map[p.id] = col_idx
            col_idx += 1

        dataset.headers = headers

        # 4. Preenche linhas
        for sessao in sessoes_ids:
            # Busca TODAS as respostas deste paciente para os questionários envolvidos
            respostas_paciente = Resposta.objects.filter(
                session_key=sessao,
                pergunta__questionario__in=questionarios_ids
            )

            if not respostas_paciente.exists(): continue

            # Dados fixos
            ultima = respostas_paciente.latest('data_resposta')
            data_str = ultima.data_resposta.strftime('%d/%m/%Y %H:%M')

            perfil_nome = '-'
            sessao_obj = SessaoPaciente.objects.filter(session_key=sessao).first()
            if sessao_obj and sessao_obj.narrativa_perfil:
                perfil_nome = sessao_obj.narrativa_perfil.titulo

            # Linha base
            row = [''] * len(headers)
            row[0] = sessao
            row[1] = data_str
            row[2] = perfil_nome

            # Preenche respostas nas colunas
            for r in respostas_paciente:
                idx = perguntas_map.get(r.pergunta.id)
                if idx is not None:
                    row[idx] = r.texto_resposta

            dataset.append(row)

        response = HttpResponse(dataset.xlsx,
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="respostas_formatadas.xlsx"'
        return response


admin.site.register(Usuario, UserAdmin)