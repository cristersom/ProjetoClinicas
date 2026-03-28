from django.contrib import admin
import nested_admin
from .models import (
    Plano, Clinica, Usuario, Categoria, Narrativa,
    Cena, Escolha, Questionario, Pergunta, OpcaoResposta, Resposta
)


# ==========================================
# SAAS ADMIN (SÓ VOCÊ, O DONO, PODE VER)
# ==========================================
class SuperUserOnlyMixin:
    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(Plano)
class PlanoAdmin(SuperUserOnlyMixin, admin.ModelAdmin):
    list_display = ('nome_exibicao', 'preco', 'limite_narrativas', 'pid')
    search_fields = ('nome_exibicao',)


@admin.register(Clinica)
class ClinicaAdmin(SuperUserOnlyMixin, admin.ModelAdmin):
    list_display = ('nome', 'plano_atual', 'assinatura_ativa')
    list_filter = ('assinatura_ativa', 'plano_atual')


@admin.register(Usuario)
class UsuarioAdmin(SuperUserOnlyMixin, admin.ModelAdmin):
    list_display = ('username', 'email', 'clinica', 'is_admin_clinica')


@admin.register(Categoria)
class CategoriaAdmin(SuperUserOnlyMixin, admin.ModelAdmin):
    pass  # Clientes podem usar as categorias, mas só você pode criar/deletar


# ==========================================
# PERMISSÕES DINÂMICAS PARA CLIENTES
# ==========================================
class TenantPermissionsMixin:
    """Garante que o cliente possa usar o painel, mas só nas próprias coisas"""

    def has_module_permission(self, request): return True

    def has_view_permission(self, request, obj=None): return True

    def has_add_permission(self, request): return True

    def has_change_permission(self, request, obj=None): return True

    def has_delete_permission(self, request, obj=None): return True


# ==========================================
# JORNADA ADMIN (ISOLAMENTO MULTI-TENANT)
# ==========================================
class OpcaoRespostaInline(nested_admin.NestedTabularInline):
    model = OpcaoResposta
    extra = 0


class PerguntaInline(nested_admin.NestedStackedInline):
    model = Pergunta
    extra = 0
    inlines = [OpcaoRespostaInline]
    classes = ['collapse']


@admin.register(Questionario)
class QuestionarioAdmin(TenantPermissionsMixin, nested_admin.NestedModelAdmin):
    list_display = ('titulo', 'cena_associada')
    inlines = [PerguntaInline]

    def get_queryset(self, request):
        # A Mágica do Isolamento: Filtra a lista para mostrar só os do usuário logado
        qs = super().get_queryset(request)
        if request.user.is_superuser: return qs
        if hasattr(request.user, 'clinica') and request.user.clinica:
            return qs.filter(cena_associada__narrativa__clinica=request.user.clinica)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Impede que o cliente selecione cenas de outra pessoa no dropdown
        if db_field.name == "cena_associada" and not request.user.is_superuser:
            if hasattr(request.user, 'clinica') and request.user.clinica:
                kwargs["queryset"] = Cena.objects.filter(narrativa__clinica=request.user.clinica)
            else:
                kwargs["queryset"] = Cena.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class EscolhaInline(admin.TabularInline):
    model = Escolha
    fk_name = 'cena_origem'
    extra = 0


@admin.register(Cena)
class CenaAdmin(TenantPermissionsMixin, admin.ModelAdmin):
    list_display = ('titulo', 'narrativa', 'ordem')
    list_filter = ('narrativa',)
    inlines = [EscolhaInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser: return qs
        if hasattr(request.user, 'clinica') and request.user.clinica:
            return qs.filter(narrativa__clinica=request.user.clinica)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "narrativa" and not request.user.is_superuser:
            if hasattr(request.user, 'clinica') and request.user.clinica:
                kwargs["queryset"] = Narrativa.objects.filter(clinica=request.user.clinica)
            else:
                kwargs["queryset"] = Narrativa.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Narrativa)
class NarrativaAdmin(TenantPermissionsMixin, admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'visualizacoes', 'data_criacao')
    list_filter = ('categoria',)
    search_fields = ('titulo', 'descricao')
    exclude = ('clinica', 'visualizacoes')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser: return qs
        if hasattr(request.user, 'clinica') and request.user.clinica:
            return qs.filter(clinica=request.user.clinica)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not getattr(obj, 'clinica', None) and hasattr(request.user, 'clinica'):
            obj.clinica = request.user.clinica
        super().save_model(request, obj, form, change)


@admin.register(Resposta)
class RespostaAdmin(TenantPermissionsMixin, admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser: return qs
        if hasattr(request.user, 'clinica') and request.user.clinica:
            return qs.filter(pergunta__questionario__cena_associada__narrativa__clinica=request.user.clinica)
        return qs.none()