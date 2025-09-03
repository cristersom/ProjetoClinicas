from django.shortcuts import render
from .models import Narrativa
from django.views.generic import TemplateView, ListView, DetailView

# Create your views here.
class Homepage(TemplateView):
    template_name =  "homepage.html"

class Narrativas(ListView):
    template_name = "narrativas.html"
    model = Narrativa
# object_list -> LIsta de itens do modelo

class Detalhes(DetailView):
    template_name = "detalhes.html"
    model = Narrativa
# object -> 1 item do nosso modelo

    def get_context_data(self, **kwargs):
        context = super(Detalhes, self).get_context_data(**kwargs)
        #self.get_object()
        relacionados = Narrativa.objects.filter(categoria=self.get_object().categoria)[0:5]
        context["relacionados"] = relacionados
        return context



# def homepage(request):
# return render(request, "homepage.html")

# def narrativas (request):
# context = {}
# lista_narrativas = Narrativa.objects.all()
# context['lista_narrativas'] = lista_narrativas
#     return render(request, "narrativas.html", context)