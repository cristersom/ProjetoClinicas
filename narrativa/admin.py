from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
import nested_admin
from .models import (
    Narrativa, Cena, Escolha, Questionario, Pergunta, Usuario, Resposta,
    SessaoPaciente, OpcaoResposta, LogVisitaCena, Categoria, Plano, Clinica, PagamentoPendente
)
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from django.urls import path, reverse
from django.http import HttpResponse
from tablib import Dataset
from django.shortcuts import render
from django.utils.html import format_html
from collections import Counter
import json
from django.db.models import Count, Value
from django.db.models.functions import Coalesce

class SuperUserOnlyMixin:
    def has_module_permission(self, request):
        return request.user.is_superuser

@admin.register(Plano)
class PlanoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'preco', 'limite_narrativas', 'limite_pacientes', 'destaque', 'stripe_price_id')
    list_editable = ('preco', 'limite_narrativas', 'limite_pacientes', 'destaque')

@admin.register(Clinica)
class ClinicaAdmin(SuperUserOnlyMixin, admin.ModelAdmin):
    list_display = ('nome', 'plano_atual', 'assinatura_ativa')

@admin.register(Usuario)
class CustomUserAdmin(SuperUserOnlyMixin, UserAdmin):
    list_display = ('username', 'email', 'clinica', 'is_staff')

@admin.register(Categoria)
class CategoriaAdmin(SuperUserOnlyMixin, admin.ModelAdmin):
    list_display = ('titulo',)

@admin.register(PagamentoPendente)
class PagamentoPendenteAdmin(SuperUserOnlyMixin, admin.ModelAdmin):
    list_display = ('email', 'plano', 'data_pagamento', 'utilizado')

# ==========================================
# ISOLAMENTO MULTI-TENANT E BLINDAGEM ABSOLUTA
# ==========================================
class TenantPermissionsMixin:
    def get_clinica_atualizada(self, request):
        if hasattr(request, 'clinica_realtime') and request.clinica_realtime:
            return request.clinica_realtime
        if hasattr(request.user, 'clinica') and request.user.clinica:
            return Clinica.objects.get(id=request.user.clinica.id)
        return None

    def has_module_permission(self, request): return True
    def has_view_permission(self, request, obj=None): return True

    def has_add_permission(self, request, *args, **kwargs):
        if request.user.is_superuser: return True
        c = self.get_clinica_atualizada(request)
        if c and not c.assinatura_ativa: return False
        return True

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser: return True
        c = self.get_clinica_atualizada(request)
        if c and not c.assinatura_ativa: return False
        return True

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser: return True
        c = self.get_clinica_atualizada(request)
        if c and not c.assinatura_ativa: return False
        return True


# ==========================================
# INLINES ESTRUTURADOS EM BLOCO (STACKED) PARA MELHOR UX
# ==========================================
class EscolhaInline(TenantPermissionsMixin, admin.StackedInline):
    model = Escolha
    fk_name = 'cena_origem'
    extra = 1

class OpcaoRespostaInline(TenantPermissionsMixin, nested_admin.NestedStackedInline):
    model = OpcaoResposta
    extra = 1
    fk_name = 'pergunta'

class PerguntaInline(TenantPermissionsMixin, nested_admin.NestedStackedInline):
    model = Pergunta
    fk_name = 'questionario'
    extra = 1
    inlines = [OpcaoRespostaInline]


@admin.register(Cena)
class CenaAdmin(TenantPermissionsMixin, admin.ModelAdmin):
    list_display = ('titulo', 'narrativa', 'botao_excluir')
    list_filter = ('narrativa',)
    inlines = [EscolhaInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser: return qs
        if hasattr(request.user, 'clinica') and request.user.clinica:
            return qs.filter(narrativa__clinica=request.user.clinica) | qs.filter(narrativa__isnull=True)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "narrativa" and not request.user.is_superuser:
            kwargs["queryset"] = Narrativa.objects.filter(clinica=request.user.clinica)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def botao_excluir(self, obj):
        url = reverse('admin:narrativa_cena_delete', args=[obj.pk])
        return format_html('<a class="btn btn-sm" style="background-color:#ef4444; color:white; border:none;" href="{}" title="Excluir"><i class="fas fa-trash"></i></a>', url)
    botao_excluir.short_description = 'Ação'


@admin.register(Narrativa)
class NarrativaAdmin(TenantPermissionsMixin, admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'data_criacao', 'cena_inicial', 'links_relatorios', 'botao_excluir')
    list_filter = ('categoria',)
    search_fields = ('titulo',)

    def has_add_permission(self, request, *args, **kwargs):
        if request.user.is_superuser: return True
        c = self.get_clinica_atualizada(request)
        if c:
            if not c.assinatura_ativa:
                return False
            try:
                limite = int(c.plano_atual.limite_narrativas) if c.plano_atual and c.plano_atual.limite_narrativas else 0
                qtd_atual = Narrativa.objects.filter(clinica=c).count()
                if qtd_atual >= limite:
                    return False
            except Exception:
                pass
        return super().has_add_permission(request, *args, **kwargs)

    def get_exclude(self, request, obj=None):
        if request.user.is_superuser: return ('visualizacoes',)
        return ('clinica', 'visualizacoes')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser: return qs
        if hasattr(request.user, 'clinica') and request.user.clinica:
            return qs.filter(clinica=request.user.clinica)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and hasattr(request.user, 'clinica'):
            obj.clinica = request.user.clinica
        super().save_model(request, obj, form, change)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/relatorio_percurso/', self.admin_site.admin_view(self.relatorio_percurso_view), name='narrativa_narrativa_percurso'),
        ]
        return custom_urls + urls

    def links_relatorios(self, obj):
        url_percurso = reverse('admin:narrativa_narrativa_percurso', args=[obj.pk])
        return format_html('<a class="btn btn-sm" style="background-color:#14b8a6; color:white; border:none;" href="{}" title="Relatório de Percurso"><i class="fas fa-chart-line"></i></a>', url_percurso)
    links_relatorios.short_description = 'Relatório'

    def botao_excluir(self, obj):
        url = reverse('admin:narrativa_narrativa_delete', args=[obj.pk])
        return format_html('<a class="btn btn-sm" style="background-color:#ef4444; color:white; border:none;" href="{}" title="Excluir"><i class="fas fa-trash"></i></a>', url)
    botao_excluir.short_description = 'Ação'

    def relatorio_percurso_view(self, request, object_id, *args, **kwargs):
        narrativa_atual = self.get_object(request, object_id)
        if not request.user.is_superuser and narrativa_atual.clinica != request.user.clinica: return HttpResponse("Acesso negado.", status=403)
        todos_os_perfis = Narrativa.objects.filter(clinica=narrativa_atual.clinica) if narrativa_atual.clinica else Narrativa.objects.none()
        perfis_selecionados_ids = request.GET.getlist('narrativa_perfil_id')
        sessoes_filtradas = SessaoPaciente.objects.all()

        if perfis_selecionados_ids and 'all' not in perfis_selecionados_ids:
            perfis_ids_int = [int(pid) for pid in perfis_selecionados_ids if pid.isdigit()]
            sessoes_filtradas = sessoes_filtradas.filter(narrativa_perfil_id__in=perfis_ids_int)
        else:
            perfis_selecionados_ids = ['all']

        lista_de_session_keys = sessoes_filtradas.values_list('session_key', flat=True)
        cenas_da_narrativa = Cena.objects.filter(narrativa=narrativa_atual).order_by('id')
        visitas_base = LogVisitaCena.objects.filter(session_key__in=lista_de_session_keys, narrativa_associada=narrativa_atual)

        visitas_totais = visitas_base.values('cena_visitada').annotate(total_visitas=Coalesce(Count('id'), Value(0))).order_by('cena_visitada')
        mapa_visitas_totais = {item['cena_visitada']: item['total_visitas'] for item in visitas_totais}

        visitantes_unicos = visitas_base.values('cena_visitada').annotate(visitantes_unicos=Coalesce(Count('session_key', distinct=True), Value(0))).order_by('cena_visitada')
        mapa_visitantes_unicos = {item['cena_visitada']: item['visitantes_unicos'] for item in visitantes_unicos}

        dados_agregados_cenas, labels_grafico, data_visitas_totais, data_visitantes_unicos = [], [], [], []
        for cena in cenas_da_narrativa:
            total = mapa_visitas_totais.get(cena.id, 0)
            unicos = mapa_visitantes_unicos.get(cena.id, 0)
            dados_agregados_cenas.append({'cena_titulo': cena.titulo, 'total_visitas': total, 'visitantes_unicos': unicos})
            labels_grafico.append(cena.titulo)
            data_visitas_totais.append(total)
            data_visitantes_unicos.append(unicos)

        export_format = request.GET.get('export')
        if export_format in ['csv', 'xlsx', 'json']:
            dataset = Dataset()
            dataset.headers = ['Cena', 'Total de Visitas', 'Visitantes Únicos']
            for item in dados_agregados_cenas: dataset.append([item['cena_titulo'], item['total_visitas'], item['visitantes_unicos']])
            if export_format == 'xlsx':
                file_data, content_type = dataset.xlsx, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif export_format == 'json':
                file_data, content_type = dataset.json, 'application/json'
            else:
                file_data, content_type = dataset.csv, 'text/csv'
            response = HttpResponse(file_data, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="percurso_{narrativa_atual.id}.{export_format}"'
            return response

        return render(request, 'admin/relatorio_narrativa_percurso.html', {
            **self.admin_site.each_context(request),
            'title': f"Percurso: {narrativa_atual.titulo}",
            'dados_agregados_cenas': dados_agregados_cenas,
            'labels_grafico': json.dumps(labels_grafico),
            'data_visitas_totais': json.dumps(data_visitas_totais),
            'data_visitantes_unicos': json.dumps(data_visitantes_unicos),
            'todos_os_perfis': todos_os_perfis,
            'perfis_selecionados_ids': perfis_selecionados_ids,
        })

@admin.register(Questionario)
class QuestionarioAdmin(TenantPermissionsMixin, nested_admin.NestedModelAdmin):
    list_display = ('titulo', 'cena_associada', 'links_relatorios')
    inlines = [PerguntaInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser: return qs
        if hasattr(request.user, 'clinica') and request.user.clinica:
            return qs.filter(cena_associada__narrativa__clinica=request.user.clinica) | qs.filter(cena_associada__isnull=True)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ["cena_associada", "cena_destino"] and not request.user.is_superuser:
            kwargs["queryset"] = Cena.objects.filter(narrativa__clinica=request.user.clinica)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_urls(self):
        urls = super().get_urls()
        return [
            path('<path:object_id>/resumo/', self.admin_site.admin_view(self.resumo_agregado_view), name='narrativa_questionario_resumo_agregado'),
            path('<path:object_id>/relatorio_detalhe/', self.admin_site.admin_view(self.relatorio_detalhado_view), name='narrativa_questionario_relatorio_detalhe'),
        ] + urls

    def links_relatorios(self, obj):
        url_detalhe = reverse('admin:narrativa_questionario_relatorio_detalhe', args=[obj.pk])
        url_resumo = reverse('admin:narrativa_questionario_resumo_agregado', args=[obj.pk])
        return format_html(
            '<a class="btn btn-sm" style="background-color:#3b82f6; color:white; border:none; margin-right:5px;" href="{}" title="Detalhado"><i class="fas fa-list"></i></a>'
            '<a class="btn btn-sm" style="background-color:#14b8a6; color:white; border:none;" href="{}" title="Resumo"><i class="fas fa-chart-pie"></i></a>',
            url_detalhe, url_resumo)
    links_relatorios.short_description = 'Relatórios'

    def resumo_agregado_view(self, request, object_id, *args, **kwargs):
        questionario = self.get_object(request, object_id)
        if not request.user.is_superuser and questionario.cena_associada and questionario.cena_associada.narrativa.clinica != request.user.clinica: return HttpResponse("Acesso negado.", status=403)
        todos_os_perfis = Narrativa.objects.filter(clinica=request.user.clinica) if hasattr(request.user, 'clinica') else Narrativa.objects.all()
        perfis_selecionados_ids = request.GET.getlist('narrativa_perfil_id')
        perfis_a_processar = []

        if not perfis_selecionados_ids or 'all' in perfis_selecionados_ids:
            perfis_a_processar.append({'id': 'all', 'titulo': 'Todos os Perfis'})
            perfis_selecionados_ids = ['all']
            sessoes_filtradas = SessaoPaciente.objects.all()
        else:
            perfis_selecionados = list(Narrativa.objects.filter(id__in=perfis_selecionados_ids))
            for p in perfis_selecionados: perfis_a_processar.append({'id': p.id, 'titulo': p.titulo})
            sessoes_filtradas = SessaoPaciente.objects.filter(narrativa_perfil_id__in=perfis_selecionados_ids)

        keys = sessoes_filtradas.values_list('session_key', flat=True)
        respostas_base = Resposta.objects.filter(pergunta__questionario=questionario, session_key__in=keys)

        export_format = request.GET.get('export')
        if export_format in ['xlsx', 'csv', 'json']:
            perguntas_ordenadas = questionario.perguntas.all().order_by('id')
            dados_sessao, mapa_perfis = {}, { s.session_key: (s.narrativa_perfil.titulo if s.narrativa_perfil else "Visitante") for s in sessoes_filtradas}
            for resp in respostas_base.select_related('pergunta'):
                k = resp.session_key
                if k not in dados_sessao: dados_sessao[k] = {'perfil': mapa_perfis.get(k, "Visitante"), 'data': resp.data_resposta.strftime('%d/%m/%Y'), 'r': {}}
                dados_sessao[k]['r'][resp.pergunta.id] = resp.texto_resposta

            dataset = Dataset()
            headers = ["Sessão", "Perfil", "Data"] + [p.texto_pergunta for p in perguntas_ordenadas]
            dataset.headers = headers

            for k, d in dados_sessao.items(): dataset.append([k[:8], d['perfil'], d['data']] + [d['r'].get(p.id, "") for p in perguntas_ordenadas])

            if export_format == 'xlsx':
                file_data, content_type = dataset.xlsx, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif export_format == 'json':
                file_data, content_type = dataset.json, 'application/json'
            else:
                file_data, content_type = dataset.csv, 'text/csv'
            response = HttpResponse(file_data, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="analise_{questionario.id}.{export_format}"'
            return response

        dados_comparativos = {}
        for pergunta in questionario.perguntas.all():
            dados_comparativos[pergunta.id] = { 'pergunta_texto': pergunta.texto_pergunta, 'pergunta_tipo': pergunta.get_tipo_resposta_display(), 'pergunta_tipo_raw': pergunta.tipo_resposta, 'dados_por_perfil': [] }
            for pf in perfis_a_processar:
                rp = respostas_base.filter(pergunta=pergunta)
                if pf['id'] != 'all': rp = rp.filter(session_key__in=SessaoPaciente.objects.filter(narrativa_perfil_id=pf['id']).values_list('session_key', flat=True))
                if pergunta.tipo_resposta == "TEXTO":
                    dados_comparativos[pergunta.id]['dados_por_perfil'].append({'perfil_titulo': pf['titulo'], 'total_respostas': rp.count(), 'respostas_texto': list(rp.values_list('texto_resposta', flat=True))})
                else:
                    c = Counter()
                    if pergunta.tipo_resposta == "MULTIPLA_ESCOLHA":
                        for r in rp: c.update(r.texto_resposta.split(','))
                    else:
                        c.update(list(rp.values_list('texto_resposta', flat=True)))
                    dados_comparativos[pergunta.id]['dados_por_perfil'].append({'perfil_titulo': pf['titulo'], 'total_respostas': rp.count(), 'dados_grafico': {'labels': json.dumps(list(c.keys())), 'data': json.dumps(list(c.values())), 'tipo_grafico': 'pie' if pergunta.tipo_resposta == "UNICA_ESCOLHA" else 'bar'} })

        return render(request, 'admin/relatorio_questionario_agregado.html', {**self.admin_site.each_context(request), 'questionario': questionario, 'dados_comparativos': dados_comparativos, 'todos_os_perfis': todos_os_perfis})

    def relatorio_detalhado_view(self, request, object_id, *args, **kwargs):
        questionario = self.get_object(request, object_id)
        if not request.user.is_superuser and questionario.cena_associada and questionario.cena_associada.narrativa.clinica != request.user.clinica: return HttpResponse("Acesso negado.", status=403)
        respostas = Resposta.objects.filter(pergunta__questionario=questionario).order_by('session_key', 'pergunta__id')
        dados = {}

        export_format = request.GET.get('export')
        if export_format in ['xlsx', 'csv', 'json']:
            perguntas_ordenadas = questionario.perguntas.all().order_by('id')
            dataset = Dataset()
            dataset.headers = ["Sessão do Paciente", "Data"] + [p.texto_pergunta for p in perguntas_ordenadas]
            dados_exportacao = {}
            for r in respostas:
                if r.session_key not in dados_exportacao: dados_exportacao[r.session_key] = {'data': r.data_resposta.strftime('%d/%m/%Y %H:%M'), 'respostas': {}}
                dados_exportacao[r.session_key]['respostas'][r.pergunta.id] = r.texto_resposta
            for session_key, d in dados_exportacao.items(): dataset.append([session_key[:8], d['data']] + [d['respostas'].get(p.id, "") for p in perguntas_ordenadas])

            if export_format == 'xlsx':
                file_data, content_type = dataset.xlsx, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif export_format == 'json':
                file_data, content_type = dataset.json, 'application/json'
            else:
                file_data, content_type = dataset.csv, 'text/csv'
            response = HttpResponse(file_data, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="respostas_detalhadas_{questionario.id}.{export_format}"'
            return response

        for r in respostas:
            if r.session_key not in dados: dados[r.session_key] = []
            dados[r.session_key].append(r)
        return render(request, 'admin/relatorio_questionario_detalhe.html', {**self.admin_site.each_context(request), 'questionario': questionario, 'dados_do_relatorio': dados})


class RespostaResource(resources.ModelResource):
    class Meta:
        model = Resposta
        fields = ('id', 'session_key', 'questionario', 'pergunta_texto', 'texto_resposta', 'data_resposta')
        export_order = fields

@admin.register(Resposta)
class RespostaAdmin(TenantPermissionsMixin, ImportExportModelAdmin):
    resource_class = RespostaResource
    list_display = ('id', 'pergunta', 'session_key', 'texto_resposta', 'data_resposta')
    list_filter = ('pergunta__questionario', 'data_resposta',)

    def has_export_permission(self, request): return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser: return qs
        if hasattr(request.user, 'clinica') and request.user.clinica:
            return qs.filter(pergunta__questionario__cena_associada__narrativa__clinica=request.user.clinica)
        return qs.none()

@admin.register(SessaoPaciente)
class SessaoPacienteAdmin(TenantPermissionsMixin, admin.ModelAdmin):
    list_display = ('session_key', 'narrativa_perfil', 'data_criacao')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser: return qs
        if hasattr(request.user, 'clinica') and request.user.clinica:
            return qs.filter(narrativa_perfil__clinica=request.user.clinica)
        return qs.none()