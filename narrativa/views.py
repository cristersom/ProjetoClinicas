import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from .models import Plano, Narrativa, Clinica

# Configuração da API do Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class HomeView(TemplateView):
    """Página Inicial que lista os planos para venda"""
    template_name = "homepage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['planos'] = Plano.objects.all()
        return context


class LoginView(DjangoLoginView):
    """View de Login que o seu urls.py está procurando"""
    template_name = "login.html"

    def get_success_url(self):
        return "/minhas-narrativas/"  # Redireciona para o sistema após logar


class PlanosView(TemplateView):
    """Página secundária de listagem de planos"""
    template_name = "planos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['planos'] = Plano.objects.all()
        return context


class MinhasNarrativasView(LoginRequiredMixin, ListView):
    """O coração do seu sistema: lista as narrativas da clínica do usuário"""
    model = Narrativa
    template_name = "narrativas.html"
    context_object_name = "narrativas"

    def get_queryset(self):
        # Filtra para mostrar apenas as narrativas da clínica do médico logado
        return Narrativa.objects.filter(clinica=self.request.user.clinica)


def criar_checkout_sessao(request, price_id):
    """Lógica que envia o cliente para o checkout do Stripe"""
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=request.build_absolute_uri('/sucesso/') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri('/'),
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return JsonResponse({'error': str(e)})


def sucesso_pagamento(request):
    """Tela exibida após a compra ser concluída"""
    return render(request, 'sucesso.html')