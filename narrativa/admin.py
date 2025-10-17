from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
import nested_admin # Importa a biblioteca
from .models import (
    Narrativa, Cena, Escolha, Questionario, Pergunta, Usuario, Resposta,
    SessaoPaciente, OpcaoResposta
)
from import_export.admin import ImportExportModelAdmin
from import_export import resources

# --- Classes de customização (Exportação e Filtro) - Nenhuma mudança ---
class RespostaResource(resources.ModelResource): # ... (código existente)
class NarrativaPerfilFilter(admin.SimpleListFilter): # ... (código existente)

# --- Classes Inline para edição com nested_admin ---
class EscolhaInline(admin.TabularInline):
    model = Escolha
    fk_name = 'cena_origem'
    extra = 1

class OpcaoRespostaInline(nested_admin.NestedTabularInline):
    model = OpcaoResposta
    extra = 1
    fk_name = 'pergunta'

class PerguntaInline(nested_admin.NestedTabularInline):
    model = Pergunta
    fk_name = 'questionario'
    extra = 1
    # A mágica: aninhamos o inline de opções DENTRO do inline de perguntas
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
    list_display = ('titulo', 'cena_associada')
    inlines = [PerguntaInline]

# ... (O resto do seu admin.py com SessaoPacienteAdmin, RespostaAdmin, etc. continua igual) ...
@admin.register(SessaoPaciente)
class SessaoPacienteAdmin(admin.ModelAdmin): # ...
@admin.register(Resposta)
class RespostaAdmin(ImportExportModelAdmin): # ...
admin.site.register(Usuario, UserAdmin)
# O PerguntaAdmin separado não é mais necessário