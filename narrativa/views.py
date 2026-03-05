import stripe
from django.conf import settings
from django.shortcuts import redirect, render
from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy, reverse

# Configuração da chave
stripe.api_key = settings.STRIPE_SECRET_KEY

class HomeView(TemplateView):
    template_name = "homepage.html"

class PlanosView(TemplateView):
    template_name = "planos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # IDs que vimos no seu log (Produção)
        context['planos'] = [
            {'nome': 'Básico', 'pid': 'price_1T5AoqKTeUlTkVK7eSB2CmBE', 'descricao': '5 narrativas e 100 respostas/mês.'},
            {'nome': 'Profissional', 'pid': 'price_1T5ApbKTeUlTkVK7lJkOQxg5', 'descricao': 'Narrativas ilimitadas.'},
            {'nome': 'Avançado', 'pid': 'price_1T5AqEKTeUlTkVK7Lcoie2I5', 'descricao': 'Suporte total e relatórios.'},
        ]
        return context

class LoginView(TemplateView): # View simples de login para evitar erro de rota
    template_name = "login.html"

def criar_checkout_sessao(request, price_id):
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=request.build_absolute_uri(reverse('narrativa:sucesso_pagamento')),
            cancel_url=request.build_absolute_uri(reverse('narrativa:planos')),
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        print(f"ERRO STRIPE: {e}")
        return redirect('narrativa:planos')

def sucesso_pagamento(request):
    return render(request, 'sucesso.html')