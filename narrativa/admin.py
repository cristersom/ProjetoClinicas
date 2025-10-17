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

# --- Classes de customização (Exportação e Filtro) - Nenhuma mudança ---
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

# --- ATUALIZAÇÃO PRINCIPAL: O 'ATALHO INTELIGENTE' ---
class PerguntaInline(admin.TabularInline):
    model