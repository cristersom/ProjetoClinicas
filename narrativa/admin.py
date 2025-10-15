from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.contrib.auth.admin import UserAdmin
from .models import (
    Narrativa, Cena, Escolha, Questionario, Pergunta, Usuario, Resposta,
    SessaoPaciente
)
from import_export.admin import ImportExportModelAdmin
from import_export import resources

# --- RESOURCE ATUALIZADO: Busca o perfil da Narrativa ---
class RespostaResource(resources.ModelResource):
    questionario = resources.Field(attribute='pergunta__questionario__titulo', column_name='Questionário')
    perfil_narrativa = resources.Field(column_name='Perfil (Narrativa)')

    class Meta:
        model = Resposta
        fields = ('id', 'session_key', 'perfil_narrativa', 'questionario', 'pergunta__texto_pergunta', 'texto_resposta', 'data_resposta')
        export_order = fields

    def dehydrate_perfil_narrativa(self, resposta):
        try:
            sessao = SessaoPaciente.objects.get(session_key=resposta.session_key)
            if sessao.narrativa_perfil:
                return sessao.narrativa_perfil.titulo
        except SessaoPaciente.DoesNotExist:
            return 'Não definido'
        return 'Não definido'

# --- FILTRO ATUALIZADO: Filtra por Narrativa ---
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

class PerguntaInline(admin.TabularInline):
    model = Pergunta
    fk_name = 'questionario'
    extra = 1

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
class QuestionarioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'cena_associada')
    inlines = [PerguntaInline]
    change_list_template = "admin/narrativa/questionario/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('relatorios/', self.admin_site.admin_view(self.view_relatorios_lista), name='narrativa_questionario_relatorios'),
            path('<int:object_id>/relatorio/', self.admin_site.admin_view(self.view_relatorio_detalhe), name='narrativa_questionario_relatorio_detalhe'),
        ]
        return custom_urls + urls

    def view_relatorios_lista(self, request):
        questionarios = Questionario.objects.all()
        context = dict(self.admin_site.each_context(request), questionarios=questionarios)
        return render(request, "admin/relatorio_questionarios_lista.html", context)

    def view_relatorio_detalhe(self, request, object_id):
        questionario = Questionario.objects.get(pk=object_id)
        respostas = Resposta.objects.filter(pergunta__questionario=questionario).order_by('session_key', 'pergunta__id')
        dados_agrupados = {}
        for resposta in respostas:
            if resposta.session_key not in dados_agrupados:
                dados_agrupados[resposta.session_key] = []
            dados_agrupados[resposta.session_key].append(resposta)
        context = dict(self.admin_site.each_context(request), questionario=questionario, dados_do_relatorio=dados_agrupados)
        return render(request, "admin/relatorio_questionario_detalhe.html", context)

# --- 'PerfilAdmin' REMOVIDO ---

@admin.register(SessaoPaciente)
class SessaoPacienteAdmin(admin.ModelAdmin):
    # --- ATUALIZADO PARA 'narrativa_perfil' ---
    list_display = ('session_key_abreviada', 'narrativa_perfil', 'data_criacao')
    list_filter = ('narrativa_perfil',)
    readonly_fields = ('session_key', 'narrativa_perfil', 'data_criacao')
    def session_key_abreviada(self, obj):
        return obj.session_key[:8] + '...'
    session_key_abreviada.short_description = 'Sessão do Paciente'

@admin.register(Resposta)
class RespostaAdmin(ImportExportModelAdmin):
    resource_class = RespostaResource
    list_display = ('id', 'questionario_associado', 'pergunta', 'session_key_abreviada', 'texto_resposta', 'data_resposta')
    # --- FILTRO ATUALIZADO ---
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