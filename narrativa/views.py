from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages
from .models import Narrativa, Usuario, Cena, Questionario, Pergunta, Resposta, SessaoPaciente
from .forms import CriarContaForm, FormHomepage
from django.views.generic import ListView, DetailView, FormView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin


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


class Detalhes(LoginRequiredMixin, DetailView):
    template_name = "detalhes.html"
    model = Narrativa

    def get(self, request, *args, **kwargs):
        narrativa = self.get_object()
        narrativa.visualizacoes += 1
        narrativa.save()
        usuario = request.user
        usuario.narrativas_vistas.add(narrativa)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(Detalhes, self).get_context_data(**kwargs)
        relacionados = Narrativa.objects.filter(categoria=self.get_object().categoria).order_by('-visualizacoes')[0:5]
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


class PerfilView(LoginRequiredMixin, UpdateView):
    template_name = "perfil.html"
    model = Usuario
    fields = ['first_name', 'last_name', 'email']

    def get_success_url(self):
        return reverse('narrativa:narrativas')


class Criarconta(FormView):
    template_name = "criarconta.html"
    form_class = CriarContaForm

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('narrativa:login')


class PacienteNarrativas(ListView):
    template_name = "paciente_narrativas.html"
    model = Narrativa


class PacienteDetalhes(DetailView):
    template_name = "paciente_detalhes.html"
    model = Narrativa

    def get_context_data(self, **kwargs):
        context = super(PacienteDetalhes, self).get_context_data(**kwargs)
        relacionados = Narrativa.objects.filter(categoria=self.get_object().categoria).order_by('-visualizacoes')[0:5]
        context["relacionados"] = relacionados
        return context


def iniciar_jornada_paciente(request, narrativa_id):
    narrativa = get_object_or_404(Narrativa, pk=narrativa_id)

    # --- NOVA LÓGICA DE PERFIL ---
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    # Tenta criar um registro de SessaoPaciente. Se já existir, não faz nada.
    # Isso garante que apenas a PRIMEIRA narrativa escolhida seja salva como perfil.
    SessaoPaciente.objects.get_or_create(
        session_key=session_key,
        defaults={'narrativa_perfil': narrativa}
    )
    # --- FIM DA NOVA LÓGICA ---

    if not narrativa.cena_inicial:
        messages.warning(request, f"A jornada '{narrativa.titulo}' ainda não está pronta para ser iniciada.")
        return redirect('narrativa:paciente_narrativas')

    return redirect('narrativa:exibir_cena_paciente', cena_id=narrativa.cena_inicial.id)


def exibir_cena_paciente(request, cena_id):
    cena = get_object_or_404(Cena, pk=cena_id)
    try:
        todas_cenas = list(cena.narrativa.cenas.all().order_by('id'))
        total_cenas = len(todas_cenas)
        progresso_atual = todas_cenas.index(cena) + 1
        percentual = int((progresso_atual / total_cenas) * 100)
    except (ValueError, ZeroDivisionError):
        total_cenas = 0
        progresso_atual = 0
        percentual = 0
    context = {
        'cena': cena,
        'total_cenas': total_cenas,
        'progresso_atual': progresso_atual,
        'percentual': percentual,
    }
    return render(request, 'cena_paciente.html', context)


def responder_questionario(request, questionario_id):
    questionario = get_object_or_404(Questionario, pk=questionario_id)
    if request.method == "POST":
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        for pergunta in questionario.perguntas.all():
            if pergunta.tipo_resposta == "MULTIPLA_ESCOLHA":
                respostas = request.POST.getlist(f'pergunta_{pergunta.id}')
                texto_resposta = ",".join(respostas)
            else:
                texto_resposta = request.POST.get(f'pergunta_{pergunta.id}')
            if texto_resposta:
                Resposta.objects.create(
                    pergunta=pergunta,
                    session_key=session_key,
                    texto_resposta=texto_resposta
                )
        return redirect('narrativa:paciente_narrativas')
    context = {
        'questionario': questionario
    }
    return render(request, 'questionario.html', context)