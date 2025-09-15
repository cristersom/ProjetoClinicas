from django.shortcuts import render, redirect, reverse
from .models import Narrativa, Usuario
from .forms import CriarContaForm, FormHomepage
from django.views.generic import TemplateView, ListView, DetailView, FormView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
# Create your views here.
class Homepage(FormView):
    template_name = "homepage.html"
    form_class = FormHomepage

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('narrativa:narrativas')
        else:
            return super().get(request, *args, **kwargs)

    def get_success_url(self):
        email = self.request.POST.get("email")
        usuarios = Usuario.objects.filter(email=email)
        if usuarios:
            return reverse('narrativa:login')
        else:
            return reverse('narrativa:criarconta')

class Narrativas(LoginRequiredMixin, ListView):
    template_name = "narrativas.html"
    model = Narrativa
# object_list -> LIsta de itens do modelo

class Detalhes(LoginRequiredMixin, DetailView):
    template_name = "detalhes.html"
    model = Narrativa
# object -> 1 item do nosso modelo

    def get(self, request, *args, **kwargs):
        narrativa = self.get_object()
        narrativa.visualizacoes += 1
        narrativa.save()
        usuario = request.user
        usuario.narrativas_vistas.add(narrativa)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(Detalhes, self).get_context_data(**kwargs)
        #self.get_object()
        relacionados = Narrativa.objects.filter(categoria=self.get_object().categoria)[0:5]
        context["relacionados"] = relacionados
        return context


class Pesquisa(LoginRequiredMixin, ListView):
    template_name = "pesquisa.html"
    model = Narrativa
    def get_queryset(self):
        termo_pesquisa = self.request.GET.get('query')
        if termo_pesquisa:
            object_list = self.model.objects.filter(titulo__icontains=termo_pesquisa)
            return object_list
        else:
            return None

class Perfil(LoginRequiredMixin, TemplateView):
    template_name = "perfil.html"


class Criarconta(FormView):
    template_name = "criarconta.html"
    form_class = CriarContaForm

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('narrativa:login')

# def homepage(request):
# return render(request, "homepage.html")

# def narrativas (request):
# context = {}
# lista_narrativas = Narrativa.objects.all()
# context['lista_narrativas'] = lista_narrativas
#     return render(request, "narrativas.html", context)