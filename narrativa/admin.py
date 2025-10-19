from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
import nested_admin
from .models import (
    Narrativa, Cena, Escolha, Questionario, Pergunta, Usuario, Resposta,
    SessaoPaciente, OpcaoResposta
)
from import_export.admin import ImportExportModelAdmin
from import_export import resources

# --- Classes de customização (Exportação e Filtro) ---
# ... (código existente mantido) ...
class RespostaResource(resources.ModelResource):
    questionario = resources.Field(attribute='pergunta__questionario__titulo', column_name='Questionário')
    perfil_narrativa = resources.Field(column_name='Perfil (Narrativa)')
    class Meta: model = Resposta; fields = ('id', 'session_key', 'perfil_narrativa', 'questionario', 'pergunta__texto_pergunta', 'texto_resposta','data_resposta'); export_order = fields
    def dehydrate_perfil_narrativa(self, resposta):
        try: sessao = SessaoPaciente.objects.get(session_key=resposta.session_key); return sessao.narrativa_perfil.titulo if sessao.narrativa_perfil else 'Não definido'
        except SessaoPaciente.DoesNotExist: return 'Não definido'

class NarrativaPerfilFilter(admin.SimpleListFilter):
    title = 'por Perfil (Narrativa)'; parameter_name = 'narrativa_perfil'
    def lookups(self, request, model_admin): return [(n.id, n.titulo) for n in Narrativa.objects.all()]
    def queryset(self, request, queryset):
        if self.value(): sessoes = SessaoPaciente.objects.filter(narrativa_perfil_id=self.value()); keys = sessoes.values_list('session_key', flat=True); return queryset.filter(session_key__in=keys)
        return queryset

# --- Classes Inline ---
class EscolhaInline(admin.TabularInline):
    model = Escolha; fk_name = 'cena_origem'; extra = 1

class OpcaoRespostaInline(nested_admin.NestedTabularInline):
    model = OpcaoResposta; extra = 0; fk_name = 'pergunta'

class PerguntaInline(nested_admin.NestedTabularInline):
    model = Pergunta; fk_name = 'questionario'; extra = 1
    inlines = [OpcaoRespostaInline]

# --- Registros dos Modelos no Admin ---
@admin.register(Cena)
class CenaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'narrativa'); list_filter = ('narrativa',); inlines = [EscolhaInline]

@admin.register(Narrativa)
class NarrativaAdmin(admin.ModelAdmin):
   list_display = ('titulo', 'categoria', 'data_criacao', 'cena_inicial'); list_filter = ('categoria',)

@admin.register(Questionario)
class QuestionarioAdmin(nested_admin.NestedModelAdmin):
    list_display = ('titulo', 'cena_associada')
    inlines = [PerguntaInline]

    # --- CLASSE MEDIA COMENTADA PARA USAR ESTILO PADRÃO ---
    # class Media:
    #     css = {
    #         'all': ('css/custom_admin.css',)
    #     }
    #     js = (
    #         'admin/js/vendor/jquery/jquery.min.js',
    #         'admin/js/jquery.init.js',
    #         'nested_admin/dist/nested_admin.min.js',
    #         'js/questionario_admin.js',
    #     )
    # --- FIM DO COMENTÁRIO ---

@admin.register(SessaoPaciente)
class SessaoPacienteAdmin(admin.ModelAdmin):
    # ... (código existente mantido) ...
    list_display = ('session_key_abreviada', 'narrativa_perfil', 'data_criacao'); list_filter = ('narrativa_perfil',); readonly_fields = ('session_key', 'narrativa_perfil', 'data_criacao')
    def session_key_abreviada(self, obj): return obj.session_key[:8] + '...'
    session_key_abreviada.short_description = 'Sessão do Paciente'

@admin.register(Resposta)
class RespostaAdmin(ImportExportModelAdmin):
    # ... (código existente mantido) ...
    resource_class = RespostaResource; list_display = ('id', 'questionario_associado', 'pergunta', 'session_key_abreviada', 'texto_resposta', 'data_resposta'); list_filter = (NarrativaPerfilFilter, 'pergunta__questionario', 'data_resposta',); search_fields = ('texto_resposta', 'session_key'); ordering = ('session_key', 'pergunta__questionario', 'pergunta__id')
    def questionario_associado(self, obj): return obj.pergunta.questionario.titulo
    questionario_associado.short_description = 'Questionário'
    def session_key_abreviada(self, obj): return obj.session_key[:8] + '...'
    session_key_abreviada.short_description = 'Sessão do Paciente'

admin.site.register(Usuario, UserAdmin)