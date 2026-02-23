import stripe
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.views.generic import ListView, DetailView, FormView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import admin
from .models import Narrativa, Usuario, Cena, Questionario, Resposta, SessaoPaciente, LogVisitaCena, Clinica
from .forms import CriarContaForm, FormHomepage

stripe.api_key = settings.STRIPE_SECRET_KEY

class ClinicaFilterMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        if self.request.user.is_authenticated and self.request.user.clinica:
            return queryset.filter(clinica=self.request.user.clinica)
        return queryset.none()

class Homepage(FormView):
    template_name = "homepage.html"
    form_class = FormHomepage
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated: return redirect('narrativa:narrativas')
        return super().get(request, *args, **kwargs)
    def get_success_url(self): return reverse('narrativa:home')

class Criarconta(FormView):
    template_name = "criarconta.html"
    form_class = CriarContaForm
    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    def get_success_url(self): return reverse('narrativa:home')

class PlanosView(LoginRequiredMixin, TemplateView):
    template_name = 'planos.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['planos'] = [{'nome': 'Básico', 'pid': 'price_1...'}]
        return context

def criar_checkout_sessao(request, price_id):
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=request.build_absolute_uri(reverse('narrativa:narrativas')) + "?success=true",
            cancel_url=request.build_absolute_uri(reverse('narrativa:planos')),
            client_reference_id=str(request.user.clinica.id),
        )
        return redirect(checkout_session.url, code=303)
    except: return HttpResponse(status=400)

@csrf_exempt
def stripe_webhook(request): return HttpResponse(status=200)

class Narrativas(LoginRequiredMixin, ClinicaFilterMixin, ListView):
    template_name = "narrativas.html"
    model = Narrativa
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            if not request.user.clinica or not request.user.clinica.assinatura_ativa:
                return redirect('narrativa:home')
        return super().dispatch(request, *args, **kwargs)

class Detalhes(LoginRequiredMixin, DetailView):
    template_name = "detalhes.html"
    model = Narrativa

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "admin/dashboard.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        return context

class PerfilView(LoginRequiredMixin, UpdateView):
    template_name = "perfil.html"
    model = Usuario
    fields = ['first_name', 'last_name', 'email']
    def get_success_url(self): return reverse('narrativa:home')

class PacienteNarrativas(ListView):
    template_name = "paciente_narrativas.html"
    model = Narrativa

class PacienteDetalhes(DetailView):
    template_name = "paciente_detalhes.html"
    model = Narrativa

def exibir_cena_paciente(request, cena_id):
    cena = get_object_or_404(Cena, pk=cena_id)
    return render(request, 'cena_paciente.html', {'cena': cena})

def responder_questionario(request, questionario_id):
    questionario = get_object_or_404(Questionario, pk=questionario_id)
    return render(request, 'questionario.html', {'questionario': questionario})

def perfil_sessao_view(request, narrativa_id):
    narrativa = get_object_or_404(Narrativa, pk=narrativa_id)
    return render(request, 'perfil_sessao.html', {'narrativa': narrativa})

class TermosView(TemplateView): template_name = "termos.html"
class PoliticaView(TemplateView): template_name = "politica.html"
class LerTermosView(TemplateView):
    template_name = "ler_termos.html"
    def post(self, request, *args, **kwargs): return redirect('narrativa:paciente_narrativas')