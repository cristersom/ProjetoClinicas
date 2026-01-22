from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Narrativa, Cena, Clinica, Usuario, Categoria, Resposta, Questionario, LogVisitaCena, SessaoPaciente

@admin.register(Narrativa)
class NarrativaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'clinica', 'visualizacoes')
    list_filter = ('clinica',)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(clinica=request.user.clinica)
    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.clinica = request.user.clinica
        super().save_model(request, obj, form, change)

@admin.register(Clinica)
class ClinicaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug', 'assinatura_ativa')
    prepopulated_fields = {"slug": ("nome",)}
    def has_module_permission(self, request):
        return request.user.is_superuser

@admin.register(Usuario)
class UsuarioSaaSAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('SaaS', {'fields': ('clinica', 'is_admin_clinica')}),)
    list_display = ('username', 'email', 'clinica', 'is_staff')

admin.site.register([Cena, Categoria, Questionario, Resposta, LogVisitaCena, SessaoPaciente])