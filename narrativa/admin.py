from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
import nested_admin # <-- 1. Importamos a nova biblioteca
from .models import (
    Narrativa, Cena, Escolha, Questionario, Pergunta, Usuario, Resposta,
    SessaoPaciente, OpcaoResposta
)
from import_export.admin import ImportExportModelAdmin
from import_export import resources

# ... (As classes RespostaResource e NarrativaPerfilFilter continuam iguais) ...
class RespostaResource(resources.ModelResource): #...
class NarrativaPerfilFilter(admin.SimpleListFilter): #...

# --- Classes Inline para edição ---

class EscolhaInline(admin.TabularInline):
    model = Escolha
    fk_name = 'cena_origem'
    extra = 1

# --- MUDANÇAS IMPORTANTES AQUI ---
# O OpcaoRespostaInline agora herda do nested_admin
class OpcaoRespostaInline(nested_admin.NestedTabularInline):
    model = OpcaoResposta
    extra = 1

# O PerguntaInline agora herda do nested_admin e pode ter seus próprios inlines
class PerguntaInline(nested_admin.NestedTabularInline):
    model = Pergunta
    fk_name = 'questionario'
    extra = 1
    # A mágica acontece aqui: aninhamos o inline de opções DENTRO do inline de perguntas
    inlines = [OpcaoRespostaInline]

# --- Registros dos Modelos no Admin ---

# O PerguntaAdmin não é mais necessário, pois tudo é feito na tela do Questionário
# @admin.register(Pergunta) ... foi removido.

@admin.register(Cena)
class CenaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'narrativa')
    list_filter = ('narrativa',)
    inlines = [EscolhaInline]

@admin.register(Narrativa)
class NarrativaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'data_criacao', 'cena_inicial')
    list_filter = ('categoria',)

# O QuestionarioAdmin agora herda do nested_admin
@admin.register(Questionario)
class QuestionarioAdmin(nested_admin.NestedModelAdmin):
    list_display = ('titulo', 'cena_associada')
    inlines = [PerguntaInline]

# ... (O resto do seu admin.py com SessaoPacienteAdmin, RespostaAdmin, etc. continua igual) ...
@admin.register(SessaoPaciente)
class SessaoPacienteAdmin(admin.ModelAdmin): #...
@admin.register(Resposta)
class RespostaAdmin(ImportExportModelAdmin): #...

admin.site.register(Usuario, UserAdmin)