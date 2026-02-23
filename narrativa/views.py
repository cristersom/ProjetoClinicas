import stripe
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.views.generic import ListView, DetailView, FormView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Narrativa, Usuario, Cena, Questionario, Resposta, SessaoPaciente, LogVisitaCena, Clinica
from .forms import CriarContaForm, FormHomepage

stripe.api_key = settings.STRIPE_SECRET_KEY


class ClinicaFilterMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_superuser: return queryset
        if self.request.user.is_authenticated and self.request.user.clinica:
            return queryset.filter(clinica=self.request.user.clinica)
        return queryset.none()


class Homepage(FormView):
    template_name = "homepage.html"
    form_class = FormHomepage

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated: return redirect('narrativa:narrativas')
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        email = self.request.POST.get("email")
        if Usuario.objects.filter(email=email).exists(): return reverse('narrativa:login')
        return reverse('narrativa:criarconta')


class Criarconta(FormView):
    template_name = "criarconta.html"
    form_class = CriarContaForm

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self): return reverse('narrativa:login')


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except Exception:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        clinica_id = session.get('client_reference_id')
        if clinica_id:
            clinica = Clinica.objects.get(id=clinica_id)
            clinica.assinatura_ativa = True
            clinica.save()
    return HttpResponse(status=200)


class Narrativas(LoginRequiredMixin, ClinicaFilterMixin, ListView):
    template_name = "narrativas.html"
    model = Narrativa

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            if not request.user.clinica or not request.user.clinica.assinatura_ativa:
                return redirect('narrativa:planos')
        return super().dispatch(request, *args, **kwargs)