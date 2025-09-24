from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.contrib.auth.admin import UserAdmin
from .models import Narrativa, Cena, Escolha, Questionario, Pergunta, Usuario, Resposta
from import_export.admin import ImportExportModelAdmin

# Inline para Escolhas
class EscolhaInline(admin.TabularInline):
    model = Escolha
    fk_name = 'cena_origem'
    extra = 1

# Inline para Perguntas
class PerguntaInline(admin.TabularInline):
    model = Pergunta
    fk_name = 'questionario'
    extra = 1

@admin.register(Cena)
class CenaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'narrativa')
    list_filter = ('narrativa',)
    search_fields = ('titulo', 'conteudo_textual')
    inlines = [EscolhaInline]

@admin.register(Narrativa)
class NarrativaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'data_criacao', 'cena_inicial')
    list_filter = ('categoria',)
    search_fields = ('titulo', 'descricao')


@admin.register(Questionario)
class QuestionarioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'cena_associada')
    search_fields = ('titulo',)
    inlines = [PerguntaInline]
    change_list_template = "admin/narrativa/questionario/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('relatorios/', self.admin_site.admin_view(self.view_relatorios_lista),
                 name='narrativa_questionario_relatorios'),
            path('<int:object_id>/relatorio/', self.admin_site.admin_view(self.view_relatorio_detalhe),
                 name='narrativa_questionario_relatorio_detalhe'),
        ]
        return custom_urls + urls

    def view_relatorios_lista(self, request):
        questionarios = Questionario.objects.all()
        context = dict(
            self.admin_site.each_context(request),
            questionarios=questionarios,
        )
        return render(request, "admin/relatorio_questionarios_lista.html", context)

    def view_relatorio_detalhe(self, request, object_id):
        questionario = Questionario.objects.get(pk=object_id)
        respostas = Resposta.objects.filter(pergunta__questionario=questionario).order_by('session_key', 'pergunta__id')

        # A lógica de agrupamento está correta
        dados_agrupados = {}
        for resposta in respostas:
            if resposta.session_key not in dados_agrupados:
                dados_agrupados[resposta.session_key] = []
            dados_agrupados[resposta.session_key].append(resposta)

        context = dict(
            self.admin_site.each_context(request),
            questionario=questionario,
            # --- MUDANÇA SUTIL: Mudei o nome da variável para ser mais simples ---
            dados_do_relatorio=dados_agrupados,
        )
        return render(request, "admin/relatorio_questionario_detalhe.html", context)


@admin.register(Resposta)
class RespostaAdmin(ImportExportModelAdmin):
    list_display = (
    'id', 'questionario_associado', 'pergunta', 'session_key_abreviada', 'texto_resposta', 'data_resposta')
    list_filter = ('pergunta__questionario', 'data_resposta',)
    search_fields = ('texto_resposta', 'session_key')
    ordering = ('session_key', 'pergunta__questionario', 'pergunta__id')

    def questionario_associado(self, obj):
        return obj.pergunta.questionario.titulo

    questionario_associado.short_description = 'Questionário'

    # --- CORREÇÃO DO BUG DE COPIAR E COLAR ---
    def session_key_abreviada(self, obj):
        return obj.session_key[:8] + '...'

    session_key_abreviada.short_description = 'Sessão do Paciente'

# Garante que o UsuarioAdmin está registrado
admin.site.register(Usuario, UserAdmin)