from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
import nested_admin
from .models import (
    Narrativa, Cena, Escolha, Questionario, Pergunta, Usuario, Resposta,
    SessaoPaciente, OpcaoResposta
)
# --- Importações para Exportação ---
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
# ------------------------------------

# --- Outras Importações ---
from django.urls import path, reverse
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.html import format_html
from collections import Counter
import json
from django.db.models import Count # Para agregação

# Importar o formulário customizado
from .forms import PerguntaAdminForm
# ---------------------------


# --- Resource para Exportação de Narrativa ---
class NarrativaResource(resources.ModelResource):
    # Campo calculado para contar inícios
    total_inicios = fields.Field()

    class Meta:
        model = Narrativa
        fields = ('id', 'titulo', 'categoria', 'visualizacoes', 'data_criacao', 'cena_inicial__titulo', 'total_inicios') # Inclui título da cena inicial
        export_order = fields

    # Método para calcular o total de inícios para cada narrativa
    def dehydrate_total_inicios(self, narrativa):
        return SessaoPaciente.objects.filter(narrativa_perfil=narrativa).count()

    # Define o nome da coluna para cena_inicial__titulo
    def get_export_headers(self):
        headers = super().get_export_headers()
        try:
            # Renomeia o header da coluna da cena inicial
            idx = headers.index('cena_inicial__titulo')
            headers[idx] = 'Cena Inicial (Título)'
        except ValueError:
            pass # Ignora se a coluna não estiver presente
        return headers
# ---------------------------------------------


# --- Filtro de Perfil ---
class NarrativaPerfilFilter(admin.SimpleListFilter):
    title = 'por Perfil (Narrativa)' #
    parameter_name = 'narrativa_perfil' #

    def lookups(self, request, model_admin):
        return [(narrativa.id, narrativa.titulo) for narrativa in Narrativa.objects.all()] #

    def queryset(self, request, queryset):
        if self.value(): #
            sessoes = SessaoPaciente.objects.filter(narrativa_perfil_id=self.value()) #
            lista_de_session_keys = sessoes.values_list('session_key', flat=True) #
            return queryset.filter(session_key__in=lista_de_session_keys) #
        return queryset #


# --- Classes Inline ---
class EscolhaInline(admin.TabularInline):
    model = Escolha #
    fk_name = 'cena_origem' #
    extra = 1 #

class OpcaoRespostaInline(nested_admin.NestedTabularInline):
    model = OpcaoResposta #
    extra = 0 #
    fk_name = 'pergunta' #

class PerguntaInline(nested_admin.NestedTabularInline):
    model = Pergunta #
    form = PerguntaAdminForm # Usa o formulário customizado
    fk_name = 'questionario' #
    extra = 1 #
    inlines = [OpcaoRespostaInline] #


# --- Registros dos Modelos no Admin ---
@admin.register(Cena)
class CenaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'narrativa') #
    list_filter = ('narrativa',) #
    inlines = [EscolhaInline] #


@admin.register(Narrativa)
class NarrativaAdmin(ImportExportModelAdmin): # <-- MUDADO AQUI para incluir exportação
    resource_class = NarrativaResource # <-- Define o resource para exportação
    list_display = ('titulo', 'categoria', 'visualizacoes', 'data_criacao', 'cena_inicial', 'links_relatorios_narrativa') # Adicionado link
    list_filter = ('categoria',) #
    search_fields = ('titulo', 'descricao') # Adicionado campo de busca
    list_select_related = ('cena_inicial',) # Otimiza busca da cena inicial

    # --- Link para Relatório ---
    def links_relatorios_narrativa(self, obj):
        url_agregado = reverse('admin:narrativa_narrativa_relatorio_agregado') #
        url_detalhado_inicios = reverse('admin:narrativa_sessaopaciente_changelist') + f'?narrativa_perfil__id__exact={obj.pk}' #

        return format_html( #
            '<a class="button" href="{}?narrativa_id={}">Ver Inícios (Agregado)</a>&nbsp;'
            '<a class="button" href="{}">Ver Sessões Iniciadas (Detalhado)</a>',
            url_agregado, #
            obj.pk, # Passa o ID da narrativa como parâmetro para o agregado
            url_detalhado_inicios #
        )
    links_relatorios_narrativa.short_description = 'Relatórios de Uso' #
    # ---------------------------

    # --- View e URL do Relatório Agregado ---
    def get_urls(self):
        urls = super().get_urls() #
        custom_urls = [ #
            path( #
                'relatorio_agregado/', # URL única para o relatório agregado de TODAS as narrativas
                self.admin_site.admin_view(self.relatorio_agregado_view), #
                name='narrativa_narrativa_relatorio_agregado', #
            ),
        ]
        return custom_urls + urls #

    def relatorio_agregado_view(self, request, *args, **kwargs):
        # Agrupa SessaoPaciente por narrativa_perfil e conta
        dados_inicios = SessaoPaciente.objects.values('narrativa_perfil__titulo') \
                                            .annotate(total_inicios=Count('id')) \
                                            .order_by('-total_inicios') #

        dados_narrativas = Narrativa.objects.order_by('titulo').values('id', 'titulo', 'visualizacoes') #

        narrativa_id_filtrada = request.GET.get('narrativa_id') #
        narrativa_filtrada = None #
        if narrativa_id_filtrada: #
            try: #
                narrativa_filtrada = Narrativa.objects.get(pk=narrativa_id_filtrada) #
                dados_inicios = dados_inicios.filter(narrativa_perfil_id=narrativa_id_filtrada) #
            except Narrativa.DoesNotExist: #
                pass # Ignora ID inválido

        context = { #
            **self.admin_site.each_context(request), #
            'title': f"Relatório Agregado de Inícios de Narrativa {'- ' + narrativa_filtrada.titulo if narrativa_filtrada else ''}", #
            'dados_inicios': dados_inicios, #
            'dados_narrativas': dados_narrativas, # Passa dados gerais também
            'narrativa_filtrada': narrativa_filtrada, # Para saber se estamos em modo filtrado
        }

        return render(request, 'admin/relatorio_narrativas_agregado.html', context) #
    # ------------------------------------


@admin.register(Questionario)
class QuestionarioAdmin(nested_admin.NestedModelAdmin):
    list_display = ('titulo', 'cena_associada', 'links_relatorios') #
    inlines = [PerguntaInline] #

    class Media:
        css = {
            'all': ('css/admin_custom.css',) # Usa o caminho ajustado
        }

    # Funções get_urls, links_relatorios, resumo_agregado_view, relatorio_detalhado_view
    # (Mantidas da versão anterior)
    def get_urls(self):
        urls = super().get_urls() #
        custom_urls = [ #
            path( #
                '<path:object_id>/resumo/', #
                self.admin_site.admin_view(self.resumo_agregado_view), #
                name='narrativa_questionario_resumo_agregado', #
            ),
             path( #
                '<path:object_id>/relatorio_detalhe/', #
                self.admin_site.admin_view(self.relatorio_detalhado_view), #
                name='narrativa_questionario_relatorio_detalhe', #
            ),
        ]
        return custom_urls + urls #

    def links_relatorios(self, obj):
        url_detalhe = reverse('admin:narrativa_questionario_relatorio_detalhe', args=[obj.pk]) #
        url_resumo = reverse('admin:narrativa_questionario_resumo_agregado', args=[obj.pk]) #

        return format_html( #
            '<a class="button" href="{}">Ver Detalhado (por Paciente)</a>&nbsp;'
            '<a class="button" href="{}">Ver Resumo (Agregado)</a>',
            url_detalhe, #
            url_resumo #
        )
    links_relatorios.short_description = 'Relatórios' #


    def resumo_agregado_view(self, request, object_id, *args, **kwargs):
        questionario = self.get_object(request, object_id) #

        todos_os_perfis = Narrativa.objects.all() #
        perfis_selecionados_ids = request.GET.getlist('narrativa_perfil_id') #

        perfis_a_processar = [] #

        if not perfis_selecionados_ids or 'all' in perfis_selecionados_ids: #
            perfis_a_processar.append({'id': 'all', 'titulo': 'Todos os Perfis'}) #
            perfis_selecionados_ids = ['all'] #
        else:
            perfis_selecionados = list(Narrativa.objects.filter(id__in=perfis_selecionados_ids)) #
            for p in perfis_selecionados: #
                perfis_a_processar.append({'id': p.id, 'titulo': p.titulo}) #

        respostas_base = Resposta.objects.filter(pergunta__questionario=questionario) #

        dados_comparativos = {} #

        for pergunta in questionario.perguntas.all(): #

            dados_comparativos[pergunta.id] = { #
                'pergunta_texto': pergunta.texto_pergunta, #
                'pergunta_tipo': pergunta.get_tipo_resposta_display, #
                'pergunta_tipo_raw': pergunta.tipo_resposta, #
                'dados_por_perfil': [] #
            }

            for perfil_info in perfis_a_processar: #

                respostas_perfil = respostas_base.filter(pergunta=pergunta) #

                if perfil_info['id'] != 'all': #
                    sessoes = SessaoPaciente.objects.filter(narrativa_perfil_id=perfil_info['id']) #
                    lista_de_session_keys = sessoes.values_list('session_key', flat=True) #
                    respostas_perfil = respostas_perfil.filter(session_key__in=lista_de_session_keys) #

                total_respostas_perfil = respostas_perfil.count() #

                dados_perfil_para_pergunta = { #
                    'perfil_titulo': perfil_info['titulo'], #
                    'total_respostas': total_respostas_perfil, #
                    'dados_grafico': None, #
                    'respostas_texto': None #
                }

                if pergunta.tipo_resposta == "TEXTO": #
                    dados_perfil_para_pergunta['respostas_texto'] = list(respostas_perfil.values_list('texto_resposta', flat=True)) #

                elif pergunta.tipo_resposta in ["UNICA_ESCOLHA", "ESCALA_5", "MULTIPLA_ESCOLHA"]: #
                    contador = Counter() #

                    if pergunta.tipo_resposta == "MULTIPLA_ESCOLHA": #
                        for resp in respostas_perfil: #
                            opcoes_selecionadas = resp.texto_resposta.split(',') #
                            contador.update(opcoes_selecionadas) #
                    else:
                        lista_de_textos = list(respostas_perfil.values_list('texto_resposta', flat=True)) #
                        contador.update(lista_de_textos) #

                    labels = list(contador.keys()) #
                    data = list(contador.values()) #

                    dados_perfil_para_pergunta['dados_grafico'] = { #
                        'labels': json.dumps(labels), #
                        'data': json.dumps(data), #
                        'tipo_grafico': 'pie' if pergunta.tipo_resposta == "UNICA_ESCOLHA" else 'bar' #
                    }

                dados_comparativos[pergunta.id]['dados_por_perfil'].append(dados_perfil_para_pergunta) #

        context = { #
            **self.admin_site.each_context(request), #
            'title': f"Resumo Comparativo: {questionario.titulo}", #
            'questionario': questionario, #
            'dados_comparativos': dados_comparativos, #
            'todos_os_perfis': todos_os_perfis, #
            'perfis_selecionados_ids': perfis_selecionados_ids, #
        }

        return render(request, 'admin/relatorio_questionario_agregado.html', context) #

    def relatorio_detalhado_view(self, request, object_id, *args, **kwargs):
        questionario = self.get_object(request, object_id) #

        respostas = Resposta.objects.filter(pergunta__questionario=questionario).order_by('session_key', 'pergunta__id') #

        dados_do_relatorio = {} #
        for resposta in respostas: #
            if resposta.session_key not in dados_do_relatorio: #
                dados_do_relatorio[resposta.session_key] = [] #
            dados_do_relatorio[resposta.session_key].append(resposta) #

        context = { #
            **self.admin_site.each_context(request), #
            'title': f"Relatório: {questionario.titulo}", #
            'questionario': questionario, #
            'dados_do_relatorio': dados_do_relatorio, #
        }
        return render(request, 'admin/relatorio_questionario_detalhe.html', context) #


@admin.register(SessaoPaciente)
class SessaoPacienteAdmin(admin.ModelAdmin):
    list_display = ('session_key_abreviada', 'narrativa_perfil', 'data_criacao') #
    list_filter = ('narrativa_perfil',) #
    readonly_fields = ('session_key', 'narrativa_perfil', 'data_criacao') #

    def session_key_abreviada(self, obj):
        return obj.session_key[:8] + '...' #
    session_key_abreviada.short_description = 'Sessão do Paciente' #


# --- Define RespostaResource ANTES de RespostaAdmin ---
class RespostaResource(resources.ModelResource):
    questionario = fields.Field(attribute='pergunta__questionario__titulo', column_name='Questionário') #
    perfil_narrativa = fields.Field(column_name='Perfil (Narrativa)') #

    class Meta:
        model = Resposta #
        fields = ('id', 'session_key', 'perfil_narrativa', 'questionario', 'pergunta__texto_pergunta', 'texto_resposta', #
                  'data_resposta')
        export_order = fields #

    def dehydrate_perfil_narrativa(self, resposta):
        try: #
            sessao = SessaoPaciente.objects.get(session_key=resposta.session_key) #
            if sessao.narrativa_perfil: #
                return sessao.narrativa_perfil.titulo #
        except SessaoPaciente.DoesNotExist: #
            return 'Não definido' #
        return 'Não definido' #
# ----------------------------------------------------

@admin.register(Resposta)
class RespostaAdmin(ImportExportModelAdmin):
    resource_class = RespostaResource # Usa o resource para exportação
    list_display = ( #
    'id', 'questionario_associado', 'pergunta', 'session_key_abreviada', 'texto_resposta', 'data_resposta')
    list_filter = (NarrativaPerfilFilter, 'pergunta__questionario', 'data_resposta',) #
    search_fields = ('texto_resposta', 'session_key') #
    ordering = ('session_key', 'pergunta__questionario', 'pergunta__id') #

    # Funções get_urls e resumo_global_view (Mantidas da versão anterior)
    def get_urls(self):
        urls = super().get_urls() #
        custom_urls = [ #
            path( #
                'resumo_global/', #
                self.admin_site.admin_view(self.resumo_global_view), #
                name='narrativa_resposta_resumo_global', #
            ),
        ]
        return custom_urls + urls #

    def resumo_global_view(self, request, *args, **kwargs):

        todos_os_perfis = Narrativa.objects.all() #
        todos_os_questionarios = Questionario.objects.all() #

        perfis_selecionados_ids = request.GET.getlist('narrativa_perfil_id') #
        questionarios_selecionados_ids = request.GET.getlist('questionario_id') #

        respostas_base = Resposta.objects.all() #

        if questionarios_selecionados_ids and 'all' not in questionarios_selecionados_ids: #
            respostas_base = respostas_base.filter(pergunta__questionario_id__in=questionarios_selecionados_ids) #
        else:
            questionarios_selecionados_ids = ['all'] #

        perfis_a_processar = [] #
        if not perfis_selecionados_ids or 'all' in perfis_selecionados_ids: #
            perfis_a_processar.append({'id': 'all', 'titulo': 'Todos os Perfis (Agregado)'}) #
            perfis_selecionados_ids = ['all'] #
        else:
            perfis_selecionados = list(Narrativa.objects.filter(id__in=perfis_selecionados_ids)) #
            for p in perfis_selecionados: #
                perfis_a_processar.append({'id': p.id, 'titulo': p.titulo}) #


        if 'all' in questionarios_selecionados_ids: #
            perguntas = Pergunta.objects.all().order_by('questionario__id', 'id') #
        else:
            perguntas = Pergunta.objects.filter(questionario_id__in=questionarios_selecionados_ids).order_by('questionario__id', 'id') #

        dados_comparativos = {} #

        for pergunta in perguntas: #

            dados_comparativos[pergunta.id] = { #
                'pergunta_texto': f"({pergunta.questionario.titulo}) - {pergunta.texto_pergunta}", # Adiciona nome do Q.
                'pergunta_tipo': pergunta.get_tipo_resposta_display, #
                'pergunta_tipo_raw': pergunta.tipo_resposta, #
                'dados_por_perfil': [] #
            }

            for perfil_info in perfis_a_processar: #

                respostas_perfil = respostas_base.filter(pergunta=pergunta) #

                if perfil_info['id'] != 'all': #
                    sessoes = SessaoPaciente.objects.filter(narrativa_perfil_id=perfil_info['id']) #
                    lista_de_session_keys = sessoes.values_list('session_key', flat=True) #
                    respostas_perfil = respostas_perfil.filter(session_key__in=lista_de_session_keys) #

                total_respostas_perfil = respostas_perfil.count() #

                dados_perfil_para_pergunta = { #
                    'perfil_titulo': perfil_info['titulo'], #
                    'total_respostas': total_respostas_perfil, #
                    'dados_grafico': None, #
                    'respostas_texto': None #
                }

                if pergunta.tipo_resposta == "TEXTO": #
                    dados_perfil_para_pergunta['respostas_texto'] = list(respostas_perfil.values_list('texto_resposta', flat=True)) #

                elif pergunta.tipo_resposta in ["UNICA_ESCOLHA", "ESCALA_5", "MULTIPLA_ESCOLHA"]: #
                    contador = Counter() #

                    if pergunta.tipo_resposta == "MULTIPLA_ESCOLHA": #
                        for resp in respostas_perfil: #
                            opcoes_selecionadas = resp.texto_resposta.split(',') #
                            contador.update(opcoes_selecionadas) #
                    else:
                        lista_de_textos = list(respostas_perfil.values_list('texto_resposta', flat=True)) #
                        contador.update(lista_de_textos) #

                    labels = list(contador.keys()) #
                    data = list(contador.values()) #

                    dados_perfil_para_pergunta['dados_grafico'] = { #
                        'labels': json.dumps(labels), #
                        'data': json.dumps(data), #
                        'tipo_grafico': 'pie' if pergunta.tipo_resposta == "UNICA_ESCOLHA" else 'bar' #
                    }

                dados_comparativos[pergunta.id]['dados_por_perfil'].append(dados_perfil_para_pergunta) #

        context = { #
            **self.admin_site.each_context(request), #
            'title': "Relatório Global Comparativo de Respostas", #
            'dados_comparativos': dados_comparativos, #
            'todos_os_perfis': todos_os_perfis, #
            'perfis_selecionados_ids': perfis_selecionados_ids, #
            'todos_os_questionarios': todos_os_questionarios, #
            'questionarios_selecionados_ids': questionarios_selecionados_ids, #
        }

        return render(request, 'admin/relatorio_resumo_global.html', context) #


    def questionario_associado(self, obj):
        return obj.pergunta.questionario.titulo #
    questionario_associado.short_description = 'Questionário' #

    def session_key_abreviada(self, obj):
        return obj.session_key[:8] + '...' #
    session_key_abreviada.short_description = 'Sessão do Paciente' #


# Registra o usuário customizado
admin.site.register(Usuario, UserAdmin) #