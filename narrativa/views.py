import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, CreateView, DetailView
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model, login, logout
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Plano, Narrativa, Clinica, Cena, Questionario, Pergunta, Resposta
from .forms import CadastroForm

stripe.api_key = settings.STRIPE_SECRET_KEY
Usuario = get_user_model()


# ==========================================
# 1. INSTITUCIONAL E AUTENTICAÇÃO
# ==========================================
class HomeView(TemplateView):
    template_name = "homepage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['planos'] = Plano.objects.all()
        return context


class LoginView(DjangoLoginView):
    template_name = "login.html"

    def get_success_url(self):
        return reverse_lazy("narrativa:narrativas")


@login_required
def custom_logout(request):
    logout(request)
    return redirect('narrativa:home')


class CriarContaView(CreateView):
    template_name = "criarconta.html"
    form_class = CadastroForm
    success_url = reverse_lazy('narrativa:planos')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


# ==========================================
# 2. SAAS E PAGAMENTOS (STRIPE)
# ==========================================
class PlanosView(TemplateView):
    template_name = "planos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['planos'] = Plano.objects.all()
        return context


def criar_checkout_sessao(request, price_id):
    try:
        email_preenchido = request.user.email if request.user.is_authenticated else None
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=email_preenchido,
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=request.build_absolute_uri('/sucesso/'),
            cancel_url=request.build_absolute_uri('/planos/'),
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return JsonResponse({'error': str(e)})


@login_required
def sucesso_pagamento(request):
    return render(request, 'sucesso.html')


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        email_cliente = session.get('customer_details', {}).get('email')
        if email_cliente:
            usuario, created = Usuario.objects.get_or_create(email=email_cliente,
                                                             defaults={'username': email_cliente, 'is_staff': True,
                                                                       'is_admin_clinica': True})
            if created:
                usuario.set_unusable_password()
                usuario.save()
            if not usuario.clinica:
                nova_clinica = Clinica.objects.create(nome=f"Clínica de {email_cliente}")
                usuario.clinica = nova_clinica
                usuario.save()
            usuario.clinica.assinatura_ativa = True
            usuario.clinica.stripe_customer_id = session.get('customer')
            usuario.clinica.stripe_subscription_id = session.get('subscription')
            usuario.clinica.save()
    return HttpResponse(status=200)


# ==========================================
# 3. PAINEL DA CLÍNICA
# ==========================================
class MinhasNarrativasView(LoginRequiredMixin, ListView):
    model = Narrativa
    template_name = "narrativas.html"
    context_object_name = "narrativas"

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Narrativa.objects.all()
        if hasattr(self.request.user, 'clinica') and self.request.user.clinica:
            return Narrativa.objects.filter(clinica=self.request.user.clinica)
        return Narrativa.objects.none()


# ==========================================
# 4. FLUXO INTERATIVO DO PACIENTE
# ==========================================
class PacienteDetalhesView(DetailView):
    model = Narrativa
    template_name = "paciente_detalhes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Exibe outras narrativas da mesma clínica
        context['relacionados'] = Narrativa.objects.filter(clinica=self.object.clinica).exclude(id=self.object.id)[:4]
        return context


def iniciar_jornada_paciente(request, narrativa_id):
    narrativa = get_object_or_404(Narrativa, id=narrativa_id)
    narrativa.visualizacoes += 1
    narrativa.save()

    if not request.session.session_key: request.session.create()

    primeira_cena = narrativa.cenas.order_by('ordem').first()
    if primeira_cena: return redirect('narrativa:exibir_cena_paciente', cena_id=primeira_cena.id)
    return redirect('narrativa:paciente_detalhes', pk=narrativa.id)


def exibir_cena_paciente(request, cena_id):
    cena = get_object_or_404(Cena, id=cena_id)
    total_cenas = cena.narrativa.cenas.count() if cena.narrativa else 1
    percentual = int((cena.ordem / total_cenas) * 100) if total_cenas > 0 else 0
    return render(request, 'cena_paciente.html', {'cena': cena, 'total_cenas': total_cenas, 'percentual': percentual})


def responder_questionario(request, cena_id, questionario_id):
    cena = get_object_or_404(Cena, id=cena_id)
    questionario = get_object_or_404(Questionario, id=questionario_id, cena_associada=cena)
    if not request.session.session_key: request.session.create()
    session_key = request.session.session_key

    if request.method == 'POST':
        for pergunta in questionario.perguntas.all():
            resposta_key = f'pergunta_{pergunta.id}'
            if pergunta.tipo_resposta in ['TEXTO', 'ESCALA_5', 'UNICA_ESCOLHA']:
                texto = request.POST.get(resposta_key)
                if texto: Resposta.objects.create(pergunta=pergunta, texto_resposta=texto, session_key=session_key)
            elif pergunta.tipo_resposta == 'MULTIPLA_ESCOLHA':
                textos = request.POST.getlist(resposta_key)
                for texto in textos: Resposta.objects.create(pergunta=pergunta, texto_resposta=texto,
                                                             session_key=session_key)
        return redirect('narrativa:exibir_cena_paciente', cena_id=cena.id)

    return render(request, 'questionario.html', {'questionario': questionario, 'cena': cena})


def perfil_sessao(request, narrativa_id):
    narrativa = get_object_or_404(Narrativa, id=narrativa_id)
    return render(request, 'perfil_sessao.html', {
        'narrativa': narrativa, 'nome_perfil': "Paciente", 'cenas_visitadas': 1,
        'total_cenas': narrativa.cenas.count(), 'progresso_cenas_pct': 50,
        'questionarios_respondidos': 0,
        'total_questionarios': narrativa.cenas.filter(questionarios__isnull=False).count(),
        'progresso_questionarios_pct': 0,
    })