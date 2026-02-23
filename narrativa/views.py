import stripe
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.views.generic import ListView, DetailView, FormView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Narrativa, Usuario, Cena, Questionario, Resposta, Clinica

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
    from .forms import FormHomepage
    form_class = FormHomepage
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated: return redirect('narrativa:narrativas')
        return super().get(request, *args, **kwargs)
    def get_success_url(self): return reverse('narrativa:home')

class Criarconta(FormView):
    template_name = "criarconta.html"
    from .forms import CriarContaForm
    form_class = CriarContaForm
    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    def get_success_url(self): return reverse('narrativa:home')

class Narrativas(LoginRequiredMixin, ClinicaFilterMixin, ListView):
    template_name = "narrativas.html"
    model = Narrativa
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser and (not request.user.clinica or not request.user.clinica.assinatura_ativa):
            return redirect('narrativa:home')
        return super().dispatch(request, *args, **kwargs)

# Outras views (Detalhes, Dashboard, etc) devem seguir o mesmo padrão de segurança.
@csrf_exempt
def stripe_webhook(request): return HttpResponse(status=200)