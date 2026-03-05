import stripe
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from .models import Plano, Perfil

stripe.api_key = settings.STRIPE_SECRET_KEY


class HomeView(TemplateView):
    template_name = "homepage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['planos'] = Plano.objects.all()
        return context


class LoginView(DjangoLoginView):
    template_name = "login.html"

    def get_success_url(self):
        return "/minhas-narrativas/"


class MinhasNarrativasView(LoginRequiredMixin, TemplateView):
    template_name = "narrativas.html"
    # Aqui você listaria as narrativas criadas pelo médico/usuário


def criar_checkout_sessao(request, price_id):
    if not request.user.is_authenticated:
        return redirect('narrativa:login')

    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=request.user.email,
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=request.build_absolute_uri('/sucesso/'),
            cancel_url=request.build_absolute_uri('/'),
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return render(request, 'erro.html', {'erro': str(e)})


def sucesso_pagamento(request):
    # Lógica simplificada: em produção, use Webhooks do Stripe para ativar o plano
    if request.user.is_authenticated:
        perfil, created = Perfil.objects.get_or_create(user=request.user)
        perfil.assinante = True
        perfil.save()
    return render(request, 'sucesso.html')