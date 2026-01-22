from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages
from .models import Narrativa, Usuario, Cena, Questionario, Pergunta, Resposta, SessaoPaciente, LogVisitaCena, Clinica
from .forms import CriarContaForm, FormHomepage
from django.views.generic import ListView, DetailView, FormView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import admin
from django.conf import settings
import json


# --- MIXIN PARA ISOLAMENTO SAAS ---
class ClinicaFilterMixin:
    """Garante que o usuário veja apenas dados da sua clínica."""

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        if self.request.user.is_authenticated and self.request.user.clinica:
            return queryset.filter(clinica=self.request.user.clinica)
        return queryset.none()


# --- ÁREA PÚBLICA ---
class Homepage(FormView):
    template_name = "homepage.html"
    form_class = FormHomepage

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('narrativa:narrativas')
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        email = self.request.POST.get("email")
        if Usuario.objects.filter(email=email).exists():
            return reverse('narrativa:login')
        return reverse('narrativa:criarconta')


class Criarconta(FormView):
    template_name = "criarconta.html"
    form_class = CriarContaForm

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('narrativa:login')


# --- ÁREA DO ADMINISTRADOR ---
class Narrativas(LoginRequiredMixin, ClinicaFilterMixin, ListView):
    template_name = "narrativas.html"
    model = Narrativa


class Detalhes(LoginRequiredMixin, DetailView):
    template_name = "detalhes.html"
    model = Narrativa

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Narrativa.objects.all()
        return Narrativa.objects.filter(clinica=self.request.user.clinica)


class PerfilView(LoginRequiredMixin, UpdateView):
    template_name = "perfil.html"
    model = Usuario
    fields = ['first_name', 'last_name', 'email']

    def get_success_url(self):
        return reverse('narrativa:narrativas')


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "admin/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        clinica = self.request.user.clinica
        if clinica:
            context['kpi_sessoes'] = SessaoPaciente.objects.filter(narrativa_perfil__clinica=clinica).count()
            context['kpi_respostas'] = Resposta.objects.filter(
                pergunta__questionario__cena_associada__narrativa__clinica=clinica).count()
            context['kpi_narrativas'] = Narrativa.objects.filter(clinica=clinica).count()

            top = Narrativa.objects.filter(clinica=clinica).order_by('-visualizacoes')[:5]
            context['chart_top_labels'] = json.dumps([n.titulo for n in top])
            context['chart_top_data'] = json.dumps([n.visualizacoes for n in top])
        return context


# --- ÁREA DO PACIENTE ---
class PacienteNarrativas(ListView):
    template_name = "paciente_narrativas.html"
    model = Narrativa

    def get_queryset(self):
        return Narrativa.objects.all().order_by('-visualizacoes')


class PacienteDetalhes(DetailView):
    template_name = "paciente_detalhes.html"
    model = Narrativa


def exibir_cena_paciente(request, cena_id):
    cena = get_object_or_404(Cena, pk=cena_id)
    if not request.session.session_key:
        request.session.create()
    LogVisitaCena.objects.get_or_create(session_key=request.session.session_key, cena_visitada=cena,
                                        defaults={'narrativa_associada': cena.narrativa})
    return render(request, 'cena_paciente.html', {'cena': cena})


def responder_questionario(request, questionario_id):
    questionario = get_object_or_404(Questionario, pk=questionario_id)
    if request.method == "POST":
        for pergunta in questionario.perguntas.all():
            resp = request.POST.get(f'pergunta_{pergunta.id}')
            if resp:
                Resposta.objects.create(pergunta=pergunta, session_key=request.session.session_key, texto_resposta=resp)
        return redirect('narrativa:exibir_cena_paciente',
                        cena_id=questionario.cena_destino.id) if questionario.cena_destino else redirect(
            'narrativa:paciente_narrativas')
    return render(request, 'questionario.html', {'questionario': questionario})


def perfil_sessao_view(request, narrativa_id):
    narrativa = get_object_or_404(Narrativa, pk=narrativa_id)
    return render(request, 'perfil_sessao.html', {'narrativa': narrativa})


class TermosView(TemplateView): template_name = "termos.html"


class PoliticaView(TemplateView): template_name = "politica.html"


class LerTermosView(TemplateView):
    template_name = "ler_termos.html"

    def post(self, request, *args, **kwargs):
        request.session[getattr(settings, 'TERMOS_ACEITOS_KEY', 'termo_aceite_session')] = True
        return redirect('narrativa:paciente_narrativas')