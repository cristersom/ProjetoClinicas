from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from .models import (
    Narrativa, Cena, Escolha, Questionario, Pergunta, Usuario, Resposta,
    SessaoPaciente, OpcaoResposta
)
from import_export.admin import ImportExportModelAdmin
from import_export import resources

# --- Classes de customização (Exportação e Filtro) ---
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

class OpcaoRespostaInline(admin.TabularInline):
    model = OpcaoResposta
    extra = 1

class PerguntaInline(admin.TabularInline):
    model = Pergunta
    fk_name = 'questionario'
    extra = 1
    fields = ('texto_pergunta', 'tipo_resposta', 'link_para_opcoes')
    readonly_fields = ('link_para_opcoes',)

    def link_para_opcoes(self, instance):
        if instance.pk:
            if instance.tipo_resposta in ["UNICA_ESCOLHA", "MULTIPLA_ESCOLHA"]:
                url = reverse('admin:narrativa_pergunta_change', args=[instance.pk])
                return format_html('<a href="{}" target="_blank">Adicionar/Editar Opções</a>', url)
            return "Não aplicável."
        return "Salve o questionário para adicionar opções."
    link_para_opcoes.short_description = 'Ações'


# --- Registros dos Modelos no Admin ---
@admin.register(Pergunta)
class PerguntaAdmin(admin.ModelAdmin):
    list_display = ('texto_pergunta', 'questionario', 'tipo_resposta')
    list_filter = ('questionario',)
    inlines = [OpcaoRespostaInline]

@admin.register(Cena)
class CenaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'narrativa')
    inlines = [EscolhaInline]

@admin.register(Narrativa)
class NarrativaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'data_criacao', 'cena_inicial')

@admin.register(Questionario)
class QuestionarioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'cena_associada')
    inlines = [PerguntaInline]

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
    list_display = ('id', 'questionario_associado', 'pergunta', 'session_key_abreviada', 'texto_resposta', 'data_resposta')
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