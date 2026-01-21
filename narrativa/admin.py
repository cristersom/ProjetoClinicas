from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
import nested_admin
from .models import (
    Narrativa, Cena, Escolha, Questionario, Pergunta, Usuario, Resposta,
    SessaoPaciente, OpcaoResposta, LogVisitaCena,
    Categoria, Clinica  # Substituído: ConfiguracaoClinica por Clinica
)
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from django.urls import path, reverse
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.html import format_html
import json

from .forms import PerguntaAdminForm

# --- GESTÃO SAAS: CLÍNICAS ---
@admin.register(Clinica)
class ClinicaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug', 'assinatura_ativa', 'data_expiracao')
    prepopulated_fields = {"slug": ("nome",)}
    search_fields = ('nome',)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'clinica')
    list_filter = ('clinica',)

class EscolhaInline(admin.TabularInline):
    model = Escolha
    fk_name = 'cena_origem'
    extra = 1

class OpcaoRespostaInline(nested_admin.NestedTabularInline):
    model = OpcaoResposta
    extra = 0

class PerguntaInline(nested_admin.NestedTabularInline):
    model = Pergunta
    form = PerguntaAdminForm
    extra = 1
    inlines = [OpcaoRespostaInline]

@admin.register(Cena)
class CenaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'narrativa')
    list_filter = ('narrativa__clinica', 'narrativa')
    inlines = [EscolhaInline]

@admin.register(Narrativa)
class NarrativaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'clinica', 'categoria', 'visualizacoes')
    list_filter = ('clinica', 'categoria')

@admin.register(Questionario)
class QuestionarioAdmin(nested_admin.NestedModelAdmin):
    list_display = ('titulo', 'cena_associada')
    inlines = [PerguntaInline]
    class Media:
        css = {'all': ('css/admin_custom.css',)}

@admin.register(Usuario)
class UsuarioSaaSAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Gestão SaaS', {'fields': ('clinica', 'is_admin_clinica')}),
    )
    list_display = ('username', 'email', 'clinica', 'is_staff')
    list_filter = ('clinica', 'is_staff')

admin.site.register(SessaoPaciente)
admin.site.register(Resposta)
admin.site.register(LogVisitaCena)