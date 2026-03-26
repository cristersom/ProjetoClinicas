from django.contrib import admin
import nested_admin
from .models import (
    Plano, Clinica, Usuario, Categoria, Narrativa,
    Cena, Escolha, Questionario, Pergunta, OpcaoResposta, Resposta
)

# --- SAAS ADMIN ---
@admin.register(Plano)
class PlanoAdmin(admin.ModelAdmin):
    list_display = ('nome_exibicao', 'preco', 'limite_narrativas', 'pid')
    search_fields = ('nome_exibicao',)

@admin.register(Clinica)
class ClinicaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'plano_atual', 'assinatura_ativa')
    list_filter = ('assinatura_ativa', 'plano_atual')
    search_fields = ('nome', 'stripe_customer_id')

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'clinica', 'is_admin_clinica')
    list_filter = ('is_admin_clinica',)

# --- JORNADA ADMIN (NESTED ADMIN PARA QUESTIONÁRIOS) ---
class OpcaoRespostaInline(nested_admin.NestedTabularInline):
    model = OpcaoResposta
    extra = 0

class PerguntaInline(nested_admin.NestedStackedInline):
    model = Pergunta
    extra = 0
    inlines = [OpcaoRespostaInline]
    classes = ['collapse']

@admin.register(Questionario)
class QuestionarioAdmin(nested_admin.NestedModelAdmin):
    list_display = ('titulo', 'cena_associada')
    inlines = [PerguntaInline]

class EscolhaInline(admin.TabularInline):
    model = Escolha
    fk_name = 'cena_origem'
    extra = 0

@admin.register(Cena)
class CenaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'narrativa', 'ordem')
    list_filter = ('narrativa',)
    inlines = [EscolhaInline]

@admin.register(Narrativa)
class NarrativaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'clinica', 'categoria', 'visualizacoes', 'data_criacao')
    list_filter = ('clinica', 'categoria')
    search_fields = ('titulo', 'descricao')

admin.site.register(Categoria)
admin.site.register(Resposta)