import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from .models import Plano, Narrativa, Clinica

stripe.api_key = settings.STRIPE_SECRET_KEY


class HomeView(TemplateView):
    template_name = "homepage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['planos'] = Plano.objects.all()
        return context


class PlanosView(TemplateView):
    template_name = "planos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['planos'] = Plano.objects.all()
        return context


class LoginView(DjangoLoginView):
    template_name = "login.html"

    def get_success_url(self):
        return "/minhas-narrativas/"


class MinhasNarrativasView(LoginRequiredMixin, ListView):
    model = Narrativa
    template_name = "narrativas.html"
    context_object_name = "narrativas"

    def get_queryset(self):
        return Narrativa.objects.filter(clinica=self.request.user.clinica)


def criar_checkout_sessao(request, price_id):
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=request.user.email if request.user.is_authenticated else None,
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=request.build_absolute_uri('/sucesso/'),
            cancel_url=request.build_absolute_uri('/'),
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return JsonResponse({'error': str(e)})


def sucesso_pagamento(request):
    return render(request, 'sucesso.html')


@csrf_exempt
def stripe_webhook(request):
    """Ouve os avisos do Stripe e ativa a assinatura da Clínica"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        email_cliente = session.get('customer_details', {}).get('email')

        if email_cliente:
            Usuario = get_user_model()
            try:
                usuario = Usuario.objects.get(email=email_cliente)
                if usuario.clinica:
                    usuario.clinica.assinatura_ativa = True
                    usuario.clinica.stripe_customer_id = session.get('customer')
                    usuario.clinica.stripe_subscription_id = session.get('subscription')
                    usuario.clinica.save()
            except Usuario.DoesNotExist:
                pass  # Aqui você pode adicionar um log se o email não for encontrado

    return HttpResponse(status=200)