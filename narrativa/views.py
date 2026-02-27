import stripe
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.views.generic import ListView, DetailView, FormView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import admin
from .models import Narrativa, Usuario, Cena, Questionario, Resposta, SessaoPaciente, LogVisitaCena, Clinica
from .forms import CriarContaForm, FormHomepage

# Configuração da chave secreta do Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class ClinicaFilterMixin:
    """Filtra os dados para que o médico veja apenas o que pertence à sua clínica."""
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_authenticated:
            return queryset.none()
        if self.request.user.is_superuser:
            return queryset
        if self.request.user.clinica:
            return queryset.filter(clinica=self.request.user.clinica)
        return queryset.none()

# --- VIEWS PÚBLICAS ---

class Homepage(FormView):
    template_name = "homepage.html"
    form_class = FormHomepage
    def get(self, request, *args, **kwargs):
        # Se já estiver logado, manda para as narrativas, senão mostra a home
        if request.user.is_authenticated:
            return redirect('narrativa:narrativas')
        return super().get(request, *args, **kwargs)
    def get_success_url(self):
        return reverse('narrativa:home')

class Criarconta(FormView):
    template_name = "criarconta.html"
    form_class = CriarContaForm
    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    def get_success_url(self):
        return reverse('narrativa:home')

# --- FINANCEIRO E PLANOS (AGORA PÚBLICO) ---

class PlanosView(TemplateView): # Removido o LoginRequiredMixin
    template_name = 'planos.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Lista de planos com seus IDs reais
        context['planos'] = [
            {
                'nome': 'Básico',
                'pid': 'price_1T5AoqKTeUlTkVK7eSB2CmBE',
                'descricao': 'Ideal para começar: 5 narrativas e 100 respostas/mês.'
            },
            {
                'nome': 'Profissional',
                'pid': 'price_1T5ApbKTeUlTkVK7lJkOQxg5',
                'descricao': 'Para clínicas em crescimento: Narrativas ilimitadas.'
            },
            {
                'nome': 'Avançado',
                'pid': 'price_1T5AqEKTeUlTkVK7Lcoie2I5',
                'descricao': 'Acesso total, suporte prioritário e relatórios extras.'
            },
        ]
        return context

@login_required
def criar_checkout_sessao(request, price_id):
    """Protegido: O usuário precisa logar ou criar conta antes de pagar."""
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=request.user.email,
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=request.build_absolute_uri(reverse('narrativa:sucesso_pagamento')) + "?success=true",
            cancel_url=request.build_absolute_uri(reverse('narrativa:planos')),
            metadata={
                'clinica_id': request.user.clinica.id
            }
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return HttpResponse(content=str(e), status=400)

@csrf_exempt
def stripe_webhook(request):
    """Ouve o Stripe para confirmar o pagamento e ativar a assinatura no banco."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        clinica_id = session.get('metadata', {}).get('clinica_id')
        if clinica_id:
            clinica = Clinica.objects.get(id=clinica_id)
            clinica.assinatura_ativa = True
            clinica.save()
    return HttpResponse(status=200)

# --- VIEWS DO MÉDICO (PROTEGIDAS) ---

class Narrativas(LoginRequiredMixin, ClinicaFilterMixin, ListView):
    template_name = "narrativas.html"
    model = Narrativa
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('narrativa:home')
        if not request.user.is_superuser:
            if not request.user.clinica or not request.user.clinica.assinatura_ativa:
                return redirect('narrativa:planos')
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
    def get_success_url(self):
        return reverse('narrativa:home')

# --- VIEWS DO PACIENTE ---
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

# --- TERMOS E POLÍTICAS ---
class TermosView(TemplateView): template_name = "termos.html"
class PoliticaView(TemplateView): template_name = "politica.html"
class LerTermosView(TemplateView):
    template_name = "ler_termos.html"
    def post(self, request, *args, **kwargs):
        return redirect('narrativa:paciente_narrativas')

def pagamento_sucesso(request):
    return render(request, 'pagamento_sucesso.html')