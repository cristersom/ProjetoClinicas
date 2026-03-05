import stripe
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.views.generic import ListView, DetailView, FormView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Narrativa, Usuario, Cena, Questionario, Clinica
from .forms import CriarContaForm, FormHomepage

stripe.api_key = settings.STRIPE_SECRET_KEY

# --- PÚBLICAS ---

class Homepage(FormView):
    template_name = "homepage.html"
    form_class = FormHomepage
    def get(self, request, *args, **kwargs):
        # Só redireciona se estiver logado E na URL raiz '/'
        if request.user.is_authenticated and request.path == reverse('narrativa:home'):
            return redirect('narrativa:narrativas')
        return super().get(request, *args, **kwargs)
    def get_success_url(self):
        return reverse('narrativa:home')

class PlanosView(TemplateView):
    template_name = 'planos.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['planos'] = [
            {'nome': 'Básico', 'pid': 'price_1T5AoqKTeUlTkVK7eSB2CmBE', 'descricao': '5 narrativas e 100 respostas/mês.'},
            {'nome': 'Profissional', 'pid': 'price_1T5ApbKTeUlTkVK7lJkOQxg5', 'descricao': 'Narrativas ilimitadas.'},
            {'nome': 'Avançado', 'pid': 'price_1T5AqEKTeUlTkVK7Lcoie2I5', 'descricao': 'Suporte total e relatórios.'},
        ]
        return context

# --- FINANCEIRO ---

@login_required
def criar_checkout_sessao(request, price_id):
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=request.user.email,
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=request.build_absolute_uri(reverse('narrativa:sucesso_pagamento')),
            cancel_url=request.build_absolute_uri(reverse('narrativa:planos')),
            metadata={'clinica_id': request.user.clinica.id}
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return HttpResponse(str(e), status=400)

def pagamento_sucesso(request):
    return render(request, 'pagamento_sucesso.html')

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        clinica_id = session.get('metadata', {}).get('clinica_id')
        if clinica_id:
            Clinica.objects.filter(id=clinica_id).update(assinatura_ativa=True)
    return HttpResponse(status=200)

# --- MÉDICO ---
class Narrativas(LoginRequiredMixin, ListView):
    template_name = "narrativas.html"
    model = Narrativa
    def get_queryset(self):
        return Narrativa.objects.filter(clinica=self.request.user.clinica)

# (Mantenha as demais views de Detalhes, CriarConta, etc. conforme já possui)