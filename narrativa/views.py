import stripe
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.views.generic import ListView, DetailView, FormView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Narrativa, Usuario, Clinica

stripe.api_key = settings.STRIPE_SECRET_KEY

# VIEW DE PLANOS - TOTALMENTE PÚBLICA
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

# VIEW DE HOMEPAGE
class Homepage(FormView):
    template_name = "homepage.html"
    from .forms import FormHomepage
    form_class = FormHomepage
    def get(self, request, *args, **kwargs):
        # Redireciona APENAS se estiver logado E tentar acessar a Home raiz
        if request.user.is_authenticated and request.path == reverse('narrativa:home'):
            return redirect('narrativa:narrativas')
        return super().get(request, *args, **kwargs)

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
    # Lógica do webhook simplificada para brevidade
    return HttpResponse(status=200)

# Mantenha as outras views (Narrativas, Detalhes, etc.) abaixo...