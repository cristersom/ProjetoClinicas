from django.contrib import admin
from .models import Plano, Clinica, Usuario, Narrativa, Cena, Pergunta

@admin.register(Plano)
class PlanoAdmin(admin.ModelAdmin):
    list_display = ('nome_exibicao', 'preco', 'pid')

@admin.register(Clinica)
class ClinicaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'plano_atual', 'assinatura_ativa')

admin.site.register(Usuario)
admin.site.register(Narrativa)
admin.site.register(Cena)
admin.site.register(Pergunta)