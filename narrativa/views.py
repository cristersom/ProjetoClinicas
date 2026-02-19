import stripe
import json
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.views.generic import ListView, DetailView, FormView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import admin
from .models import Narrativa, Usuario, Cena, Questionario, Resposta, SessaoPaciente, LogVisitaCena, Clinica
from .forms import CriarContaForm, FormHomepage

# Configuração da API do Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


# MIXIN PARA ISOLAMENTO DE DADOS (SaaS Multi-tenant)
class ClinicaFilterMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        if self.request.user.is_authenticated and self.request.user.clinica:
            return queryset.filter(clinica=self.request.user.clinica)
        return queryset.none()


# --- VIEWS PÚBLICAS E AUTENTICAÇÃO ---
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


# --- SISTEMA DE PLANOS E STRIPE ---
class PlanosView(LoginRequiredMixin, TemplateView):
    template_name = 'planos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Price IDs que devem ser configurados no seu Stripe Dashboard
        context['planos'] = [
            {'nome': 'Básico', 'preco': '49', 'limite': 'Até 5 Jornadas', 'pid': 'price_1QuVv4C3uXz6...'},
            {'nome': 'Profissional', 'preco': '99', 'limite': 'Até 20 Jornadas', 'pid': 'price_1QuVv4C3uXz7...'},
            {'nome': 'Avançado', 'preco': '199', 'limite': 'Jornadas Ilimitadas', 'pid': 'price_1QuVv4C3uXz8...'},
            {'nome': 'Enterprise', 'preco': 'Sob Consulta', 'limite': 'Redes de Clínicas', 'pid': None},
        ]
        return context


def criar_checkout_sessao(request, price_id):
    """Redireciona para o formulário de checkout do Stripe"""
    clinica = request.user.clinica
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=request.build_absolute_uri(reverse('narrativa:narrativas')) + "?success=true",
            cancel_url=request.build_absolute_uri(reverse('narrativa:planos')),
            client_reference_id=str(clinica.id),
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return HttpResponse(str(e), status=400)


@csrf_exempt
def stripe_webhook(request):
    """Recebe a confirmação de pagamento do Stripe e ativa a conta"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    try:
        # Usa o whsec_ configurado no Heroku para validar o sinal
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except Exception:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        clinica_id = session.get('client_reference_id')

        # Busca o item pago para definir o plano e limites
        line_items = stripe.checkout.Session.list_line_items(session.id, limit=1)
        price_id = line_items.data[0].price.id

        if clinica_id:
            clinica = Clinica.objects.get(id=clinica_id)
            clinica.assinatura_ativa = True

            # Mapeamento de Limites baseado no ID do produto pago
            if "BASICO" in price_id or price_id == 'price_1QuVv4C3uXz6...':
                clinica.limite_narrativas = 5
            elif "PRO" in price_id or price_id == 'price_1QuVv4C3uXz7...':
                clinica.limite_narrativas = 20
            elif "ADV" in price_id or price_id == 'price_1QuVv4C3uXz8...':
                clinica.limite_narrativas = 9999

            clinica.save()
    return HttpResponse(status=200)


# --- ÁREA DO MÉDICO (BACK-END) ---
class Narrativas(LoginRequiredMixin, ClinicaFilterMixin, ListView):
    template_name = "narrativas.html"
    model = Narrativa

    def dispatch(self, request, *args, **kwargs):
        # Bloqueia acesso se a assinatura não estiver ativa
        if not request.user.is_superuser:
            if not request.user.clinica or not request.user.clinica.assinatura_ativa:
                return redirect('narrativa:planos')
        return super().dispatch(request, *args, **kwargs)


class Detalhes(LoginRequiredMixin, DetailView):
    template_name = "detalhes.html"
    model = Narrativa

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Narrativa.objects.all()
        return Narrativa.objects.filter(clinica=self.request.user.clinica)


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
        return context


class PerfilView(LoginRequiredMixin, UpdateView):
    template_name = "perfil.html"
    model = Usuario
    fields = ['first_name', 'last_name', 'email']

    def get_success_url(self):
        return reverse('narrativa:narrativas')


# --- ÁREA DO PACIENTE (FRONT-END) ---
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
    LogVisitaCena.objects.get_or_create(
        session_key=request.session.session_key,
        cena_visitada=cena,
        defaults={'narrativa_associada': cena.narrativa}
    )
    return render(request, 'cena_paciente.html', {'cena': cena})


def responder_questionario(request, questionario_id):
    questionario = get_object_or_404(Questionario, pk=questionario_id)
    if request.method == "POST":
        if not request.session.session_key:
            request.session.create()
        for pergunta in questionario.perguntas.all():
            resp = request.POST.get(f'pergunta_{pergunta.id}')
            if resp:
                Resposta.objects.create(
                    pergunta=pergunta,
                    session_key=request.session.session_key,
                    texto_resposta=resp
                )
        if questionario.cena_destino:
            return redirect('narrativa:exibir_cena_paciente', cena_id=questionario.cena_destino.id)
        return redirect('narrativa:paciente_narrativas')
    return render(request, 'questionario.html', {'questionario': questionario})


def perfil_sessao_view(request, narrativa_id):
    narrativa = get_object_or_404(Narrativa, pk=narrativa_id)
    return render(request, 'perfil_sessao.html', {'narrativa': narrativa})


# --- TERMOS E POLÍTICAS ---
class TermosView(TemplateView):
    template_name = "termos.html"


class PoliticaView(TemplateView):
    template_name = "politica.html"


class LerTermosView(TemplateView):
    template_name = "ler_termos.html"

    def post(self, request, *args, **kwargs):
        request.session['termo_aceite_session'] = True
        return redirect('narrativa:paciente_narrativas')