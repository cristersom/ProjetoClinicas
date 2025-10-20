from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
import nested_admin
from .models import (
    Narrativa, Cena, Escolha, Questionario, Pergunta, Usuario, Resposta,
    SessaoPaciente, OpcaoResposta
)
from import_export.admin import ImportExportModelAdmin
from import_export import resources

# --- NOVOS IMPORTS ---
from django.urls import path, reverse
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.html import format_html
from collections import Counter
import json


# ---------------------

# --- Classes de customização (Exportação e Filtro) ---
class RespostaResource(resources.ModelResource):
    questionario = resources.Field(attribute='pergunta__questionario__titulo', column_name='Questionário')
    perfil_narrativa = resources.Field(column_name='Perfil (Narrativa)')

    class Meta:
        model = Resposta
        fields = ('id', 'session_key', 'perfil_narrativa', 'questionario', 'pergunta__texto_pergunta', 'texto_resposta',
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
    list_display = ('titulo', 'categoria', 'data_criacao', 'cena_inicial')
    list_filter = ('categoria',)


@admin.register(Questionario)
class QuestionarioAdmin(nested_admin.NestedModelAdmin):
    list_display = ('titulo', 'cena_associada', 'links_relatorios')  # Modificado
    inlines = [PerguntaInline]

    # --- PASSO 1: ADICIONAR A NOVA VIEW E URL ---

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # URL para o novo resumo agregado
            path(
                '<path:object_id>/resumo/',
                self.admin_site.admin_view(self.resumo_agregado_view),
                name='narrativa_questionario_resumo_agregado',
            ),
            # (Mantemos a URL do relatório detalhado que já existia)
            path(
                '<path:object_id>/relatorio_detalhe/',
                self.admin_site.admin_view(self.relatorio_detalhado_view),
                name='narrativa_questionario_relatorio_detalhe',
            ),
        ]
        return custom_urls + urls

    # Método para criar os links na lista do admin
    def links_relatorios(self, obj):
        url_detalhe = reverse('admin:narrativa_questionario_relatorio_detalhe', args=[obj.pk])
        url_resumo = reverse('admin:narrativa_questionario_resumo_agregado', args=[obj.pk])

        return format_html(
            '<a class="button" href="{}">Ver Detalhado (por Paciente)</a>&nbsp;'
            '<a class="button" href="{}">Ver Resumo (Agregado)</a>',
            url_detalhe,
            url_resumo
        )

    links_relatorios.short_description = 'Relatórios'

    # --- PASSO 2: CRIAR A VIEW DE AGREGAÇÃO ---

    def resumo_agregado_view(self, request, object_id, *args, **kwargs):
        # Busca o questionário
        questionario = self.get_object(request, object_id)

        # Prepara os dados para o template
        dados_relatorio_agregado = []

        for pergunta in questionario.perguntas.all():
            # Busca todas as respostas para esta pergunta
            respostas = Resposta.objects.filter(pergunta=pergunta)

            total_respostas = respostas.count()
            dados_pergunta = {
                'pergunta': pergunta,
                'tipo': pergunta.tipo_resposta,
                'total_respostas': total_respostas,
                'dados_grafico': None,
                'respostas_texto': None
            }

            if pergunta.tipo_resposta == "TEXTO":
                # Se for texto, apenas lista as respostas
                dados_pergunta['respostas_texto'] = list(respostas.values_list('texto_resposta', flat=True))

            elif pergunta.tipo_resposta in ["UNICA_ESCOLHA", "ESCALA_5", "MULTIPLA_ESCOLHA"]:
                # Se for múltipla escolha ou escala, contamos as ocorrências

                # Usamos um Counter para contar facilmente
                contador = Counter()

                if pergunta.tipo_resposta == "MULTIPLA_ESCOLHA":
                    # Se for múltipla, temos que quebrar as respostas "A,B,C"
                    for resp in respostas:
                        opcoes_selecionadas = resp.texto_resposta.split(',')
                        contador.update(opcoes_selecionadas)
                else:
                    # Para escolha única ou escala, a resposta é o próprio valor
                    lista_de_textos = list(respostas.values_list('texto_resposta', flat=True))
                    contador.update(lista_de_textos)

                # Prepara os dados para o Chart.js
                labels = list(contador.keys())
                data = list(contador.values())

                dados_pergunta['dados_grafico'] = {
                    'labels': json.dumps(labels),  # Converte para JSON para o JS
                    'data': json.dumps(data),  # Converte para JSON para o JS
                    'tipo_grafico': 'pie' if pergunta.tipo_resposta == "UNICA_ESCOLHA" else 'bar'
                }

            dados_relatorio_agregado.append(dados_pergunta)

        context = {
            **self.admin_site.each_context(request),
            'title': f"Resumo Agregado: {questionario.titulo}",
            'questionario': questionario,
            'dados_relatorio_agregado': dados_relatorio_agregado,
        }

        # (O template será criado no Passo 3)
        return render(request, 'admin/relatorio_questionario_agregado.html', context)

    # View do relatório detalhado (como estava nos seus templates)
    def relatorio_detalhado_view(self, request, object_id, *args, **kwargs):
        questionario = self.get_object(request, object_id)

        # Agrupa respostas por session_key
        respostas = Resposta.objects.filter(pergunta__questionario=questionario).order_by('session_key', 'pergunta__id')

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
        # Usa o template que você já tinha
        return render(request, 'admin/relatorio_questionario_detalhe.html', context)


@admin.register(SessaoPaciente)
class SessaoPacienteAdmin(admin.ModelAdmin):
    list_display = ('session_key_abreviada', 'narrativa_perfil', 'data_criacao')
    list_filter = ('narrativa_perfil',)
    readonly_fields = ('session_key', 'narrativa_perfil', 'data_criacao')

    def session_key_abreviada(self, obj):
        return obj.session_key[:8] + '...'

    session_key_abreviada.short_description = 'Sessão do Paciente'


@admin.register(Resposta)
class RespostaAdmin(ImportExportModelAdmin):
    resource_class = RespostaResource
    list_display = (
        'id', 'questionario_associado', 'pergunta', 'session_key_abreviada', 'texto_resposta', 'data_resposta')
    list_filter = (NarrativaPerfilFilter, 'pergunta__questionario', 'data_resposta',)
    search_fields = ('texto_resposta', 'session_key')
    ordering = ('session_key', 'pergunta__questionario', 'pergunta__id')

    def questionario_associado(self, obj):
        return obj.pergunta.questionario.titulo

    questionario_associado.short_description = 'Questionário'

    def session_key_abreviada(self, obj):
        return obj.session_key[:8] + '...'

    session_key_abreviada.short_description = 'Sessão do Paciente'


admin.site.register(Usuario, UserAdmin)