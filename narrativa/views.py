from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages
from .models import Narrativa, Usuario, Cena, Questionario, Pergunta, Resposta, SessaoPaciente, LogVisitaCena, \
    ConfiguracaoClinica
from .forms import CriarContaForm, FormHomepage
from django.views.generic import ListView, DetailView, FormView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import admin
from django.conf import settings
from django.db.models import Count, Value
from django.db.models.functions import TruncDay
from django.utils import timezone
from datetime import timedelta
import json

TERMOS_ACEITOS_KEY = getattr(settings, 'TERMOS_ACEITOS_KEY', 'termo_aceite_session')


class LerTermosView(TemplateView):
    template_name = "ler_termos.html"

    def get(self, request, *args, **kwargs):
        if request.session.get(TERMOS_ACEITOS_KEY, False):
            return redirect('narrativa:paciente_narrativas')

        self.narrativa_pk = kwargs.get('narrativa_pk')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        aceite = request.POST.get('aceite', 'false').lower() == 'true'
        self.narrativa_pk = kwargs.get('narrativa_pk')

        if aceite:
            request.session[TERMOS_ACEITOS_KEY] = True
            messages.success(request, "Termos aceitos com sucesso! Bem-vindo(a) à sua jornada.")

            if self.narrativa_pk:
                return redirect('narrativa:exibir_cena_paciente', cena_id=self.narrativa_pk)
            else:
                return redirect('narrativa:paciente_narrativas')

        return redirect('narrativa:ler_termos')


class Homepage(FormView):
    template_name = "homepage.html"
    form_class = FormHomepage

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('narrativa:narrativas')
        else:
            return super().get(request, *args, **kwargs)

    def get_success_url(self):
        email = self.request.POST.get("email")
        usuarios = Usuario.objects.filter(email=email)
        if usuarios:
            return reverse('narrativa:login')
        else:
            return reverse('narrativa:criarconta')


class Narrativas(LoginRequiredMixin, ListView):
    template_name = "narrativas.html"
    model = Narrativa


class Detalhes(LoginRequiredMixin, DetailView):
    template_name = "detalhes.html"
    model = Narrativa

    def get(self, request, *args, **kwargs):
        narrativa = self.get_object()
        narrativa.visualizacoes += 1
        narrativa.save()
        usuario = request.user
        usuario.narrativas_vistas.add(narrativa)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(Detalhes, self).get_context_data(**kwargs)
        relacionados = Narrativa.objects.filter(categoria=self.get_object().categoria).order_by('-visualizacoes')[0:5]
        context["relacionados"] = relacionados
        return context


class Pesquisa(LoginRequiredMixin, ListView):
    template_name = "pesquisa.html"
    model = Narrativa

    def get_queryset(self):
        termo_pesquisa = self.request.GET.get('query')
        if termo_pesquisa:
            object_list = self.model.objects.filter(titulo__icontains=termo_pesquisa)
            return object_list
        else:
            return None


class PerfilView(LoginRequiredMixin, UpdateView):
    template_name = "perfil.html"
    model = Usuario
    fields = ['first_name', 'last_name', 'email']

    def get_success_url(self):
        return reverse('narrativa:narrativas')


class Criarconta(FormView):
    template_name = "criarconta.html"
    form_class = CriarContaForm

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('narrativa:login')


class PacienteNarrativas(ListView):
    template_name = "paciente_narrativas.html"
    model = Narrativa


class PacienteDetalhes(DetailView):
    template_name = "paciente_detalhes.html"
    model = Narrativa

    def get_context_data(self, **kwargs):
        context = super(PacienteDetalhes, self).get_context_data(**kwargs)
        relacionados = Narrativa.objects.filter(categoria=self.get_object().categoria).order_by('-visualizacoes')[0:5]
        context["relacionados"] = relacionados
        return context

    def post(self, request, *args, **kwargs):
        narrativa = self.get_object()
        return iniciar_jornada_paciente(request, narrativa.pk)


def iniciar_jornada_paciente(request, narrativa_id):
    narrativa = get_object_or_404(Narrativa, pk=narrativa_id)

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    # Garante a criação da sessão e atribuição do perfil
    sessao, created = SessaoPaciente.objects.get_or_create(
        session_key=session_key
    )

    # Se acabou de criar OU se existe mas não tem perfil: define agora.
    if created or not sessao.narrativa_perfil:
        sessao.narrativa_perfil = narrativa
        sessao.save()

    if not narrativa.cena_inicial:
        messages.warning(request, f"A jornada '{narrativa.titulo}' ainda não está pronta para ser iniciada.")
        return redirect('narrativa:paciente_narrativas')

    return redirect('narrativa:exibir_cena_paciente', cena_id=narrativa.cena_inicial.id)


def exibir_cena_paciente(request, cena_id):
    cena = get_object_or_404(Cena, pk=cena_id)

    if not request.session.session_key:
        request.session.create()

    if request.session.session_key:
        # Garante o log da visita
        LogVisitaCena.objects.get_or_create(
            session_key=request.session.session_key,
            cena_visitada=cena,
            defaults={'narrativa_associada': cena.narrativa}
        )

        # Garante o perfil caso o usuário tenha entrado direto na cena
        sessao, created = SessaoPaciente.objects.get_or_create(
            session_key=request.session.session_key
        )
        if created or not sessao.narrativa_perfil:
            sessao.narrativa_perfil = cena.narrativa
            sessao.save()

    try:
        todas_cenas = list(cena.narrativa.cenas.all().order_by('id'))
        total_cenas = len(todas_cenas)
        progresso_atual = todas_cenas.index(cena) + 1
        percentual = int((progresso_atual / total_cenas) * 100)
    except (ValueError, ZeroDivisionError):
        total_cenas = 0
        progresso_atual = 0
        percentual = 0
    context = {
        'cena': cena,
        'total_cenas': total_cenas,
        'progresso_atual': progresso_atual,
        'percentual': percentual,
    }
    return render(request, 'cena_paciente.html', context)


def responder_questionario(request, questionario_id):
    questionario = get_object_or_404(Questionario, pk=questionario_id)

    if request.method == "POST":
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

        # Garante sessão/perfil ao responder
        sessao, created = SessaoPaciente.objects.get_or_create(session_key=session_key)
        if created or not sessao.narrativa_perfil:
            if questionario.cena_associada:
                sessao.narrativa_perfil = questionario.cena_associada.narrativa
                sessao.save()

        for pergunta in questionario.perguntas.all():
            texto_resposta = None
            if pergunta.tipo_resposta == "MULTIPLA_ESCOLHA":
                respostas = request.POST.getlist(f'pergunta_{pergunta.id}')
                if respostas:
                    texto_resposta = ",".join(respostas)
            else:
                texto_resposta = request.POST.get(f'pergunta_{pergunta.id}')

            if texto_resposta:
                Resposta.objects.create(
                    pergunta=pergunta,
                    session_key=session_key,
                    texto_resposta=texto_resposta
                )

        if questionario.cena_destino:
            return redirect('narrativa:exibir_cena_paciente', cena_id=questionario.cena_destino.id)
        else:
            if questionario.cena_associada:
                return redirect('narrativa:exibir_cena_paciente', cena_id=questionario.cena_associada.id)
            return redirect('narrativa:paciente_narrativas')

    context = {
        'questionario': questionario
    }
    return render(request, 'questionario.html', context)


class AdminFAQView(LoginRequiredMixin, TemplateView):
    template_name = "admin_faq.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        return context


class TermosView(TemplateView):
    template_name = "termos.html"


class PoliticaView(TemplateView):
    template_name = "politica.html"


# --- VIEW DE PERFIL (FEEDBACK AO PACIENTE) ---
def perfil_sessao_view(request, narrativa_id):
    session_key = request.session.session_key
    if not session_key:
        return redirect('narrativa:ler_termos')

    narrativa_atual = get_object_or_404(Narrativa, pk=narrativa_id)

    # Busca ou cria sessão
    sessao_paciente, created = SessaoPaciente.objects.get_or_create(
        session_key=session_key
    )

    # Se o perfil estiver vazio, preenche com a narrativa atual (correção de bug "Visitante")
    if not sessao_paciente.narrativa_perfil:
        sessao_paciente.narrativa_perfil = narrativa_atual
        sessao_paciente.save()

    nome_perfil = sessao_paciente.narrativa_perfil.titulo

    # 1. LÓGICA CUMULATIVA (Baseada em todas as narrativas visitadas nesta sessão)
    ids_narrativas_visitadas = LogVisitaCena.objects.filter(
        session_key=session_key
    ).values_list('narrativa_associada', flat=True).distinct()

    # 2. Cálculo de Cenas
    total_cenas = Cena.objects.filter(narrativa__id__in=ids_narrativas_visitadas).count()

    cenas_visitadas = LogVisitaCena.objects.filter(
        session_key=session_key
    ).values('cena_visitada').distinct().count()

    progresso_cenas_pct = 0
    if total_cenas > 0:
        progresso_cenas_pct = int((cenas_visitadas / total_cenas) * 100)
        if progresso_cenas_pct > 100: progresso_cenas_pct = 100

    # 3. Cálculo de Questionários
    total_questionarios = Questionario.objects.filter(
        cena_associada__narrativa__id__in=ids_narrativas_visitadas
    ).count()

    questionarios_respondidos = Resposta.objects.filter(
        session_key=session_key
    ).values('pergunta__questionario').distinct().count()

    progresso_questionarios_pct = 0
    if total_questionarios > 0:
        progresso_questionarios_pct = int((questionarios_respondidos / total_questionarios) * 100)
        if progresso_questionarios_pct > 100: progresso_questionarios_pct = 100

    context = {
        'narrativa': narrativa_atual,
        'nome_perfil': nome_perfil,
        'cenas_visitadas': cenas_visitadas,
        'total_cenas': total_cenas,
        'progresso_cenas_pct': progresso_cenas_pct,
        'questionarios_respondidos': questionarios_respondidos,
        'total_questionarios': total_questionarios,
        'progresso_questionarios_pct': progresso_questionarios_pct,
    }

    return render(request, 'perfil_sessao.html', context)


# --- DASHBOARD ADMINISTRATIVO ---
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "admin/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))

        # KPIs
        total_sessoes = SessaoPaciente.objects.count()
        total_respostas = Resposta.objects.count()
        total_narrativas = Narrativa.objects.count()

        cenas_finais_ids = Cena.objects.filter(escolhas__isnull=True).values_list('id', flat=True)
        sessoes_finalizadas = LogVisitaCena.objects.filter(
            cena_visitada__id__in=cenas_finais_ids
        ).values('session_key').distinct().count()

        # Gráfico 1: Acessos (30 dias)
        trinta_dias_atras = timezone.now() - timedelta(days=30)
        acessos_diarios = LogVisitaCena.objects.filter(timestamp__gte=trinta_dias_atras) \
            .annotate(dia=TruncDay('timestamp')) \
            .values('dia') \
            .annotate(total=Count('id')) \
            .order_by('dia')

        # Tratamento para listas vazias
        if acessos_diarios:
            labels_dias = [item['dia'].strftime('%d/%m') for item in acessos_diarios]
            data_acessos = [item['total'] for item in acessos_diarios]
        else:
            labels_dias = []
            data_acessos = []

        # Gráfico 2: Top 5 Narrativas
        top_narrativas = Narrativa.objects.order_by('-visualizacoes')[:5]
        if top_narrativas:
            labels_top = [n.titulo for n in top_narrativas]
            data_top = [n.visualizacoes for n in top_narrativas]
        else:
            labels_top = []
            data_top = []

        context.update({
            'kpi_sessoes': total_sessoes,
            'kpi_respostas': total_respostas,
            'kpi_finalizadas': sessoes_finalizadas,
            'kpi_narrativas': total_narrativas,
            'chart_dias_labels': json.dumps(labels_dias),
            'chart_dias_data': json.dumps(data_acessos),
            'chart_top_labels': json.dumps(labels_top),
            'chart_top_data': json.dumps(data_top),
        })
        return context