from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages
from .models import Narrativa, Usuario, Cena, Questionario, Pergunta, Resposta, SessaoPaciente, LogVisitaCena, \
    ConfiguracaoClinica
from .forms import CriarContaForm, FormHomepage
from django.views.generic import ListView, DetailView, FormView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import admin
from django.conf import settings
from django.db.models import Count, Value

TERMOS_ACEITOS_KEY = getattr(settings, 'TERMOS_ACEITOS_KEY', 'termo_aceite_session')


class LerTermosView(TemplateView):
    template_name = "ler_termos.html"

    def get(self, request, *args, **kwargs):
        if request.session.get(TERMOS_ACEITOS_KEY, False):
            return redirect('narrativa:paciente_narrativas')

        self.narrativa_pk = kwargs.get('narrativa_pk')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        aceite = request.POST.get('aceite', 'false').lower() == 'true'
        self.narrativa_pk = kwargs.get('narrativa_pk')

        if aceite:
            request.session[TERMOS_ACEITOS_KEY] = True
            messages.success(request, "Termos aceitos com sucesso! Bem-vindo(a) à sua jornada.")

            if self.narrativa_pk:
                return redirect('narrativa:exibir_cena_paciente', cena_id=self.narrativa_pk)
            else:
                return redirect('narrativa:paciente_narrativas')

        return redirect('narrativa:ler_termos')


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

    def post(self, request, *args, **kwargs):
        narrativa = self.get_object()
        return iniciar_jornada_paciente(request, narrativa.pk)


def iniciar_jornada_paciente(request, narrativa_id):
    narrativa = get_object_or_404(Narrativa, pk=narrativa_id)

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    # Mantém a lógica: O perfil é definido pela PRIMEIRA narrativa que o paciente acessa.
    SessaoPaciente.objects.get_or_create(
        session_key=session_key,
        defaults={'narrativa_perfil': narrativa}
    )

    if not narrativa.cena_inicial:
        messages.warning(request, f"A jornada '{narrativa.titulo}' ainda não está pronta para ser iniciada.")
        return redirect('narrativa:paciente_narrativas')

    return redirect('narrativa:exibir_cena_paciente', cena_id=narrativa.cena_inicial.id)


def exibir_cena_paciente(request, cena_id):
    cena = get_object_or_404(Cena, pk=cena_id)

    if not request.session.session_key:
        request.session.create()

    # Cria o log garantindo que a narrativa_associada esteja correta
    if request.session.session_key:
        LogVisitaCena.objects.create(
            session_key=request.session.session_key,
            cena_visitada=cena,
            narrativa_associada=cena.narrativa
        )

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

        # Flag para saber se o usuário respondeu algo
        respondeu_algo = False

        for pergunta in questionario.perguntas.all():
            texto_resposta = None
            if pergunta.tipo_resposta == "MULTIPLA_ESCOLHA":
                respostas = request.POST.getlist(f'pergunta_{pergunta.id}')
                if respostas:
                    texto_resposta = ",".join(respostas)
            else:
                texto_resposta = request.POST.get(f'pergunta_{pergunta.id}')

            if texto_resposta:
                respondeu_algo = True
                Resposta.objects.create(
                    pergunta=pergunta,
                    session_key=session_key,
                    texto_resposta=texto_resposta
                )

        # IMPORTANTE: Se o usuário submeteu, mas não respondeu nada (campos vazios),
        # ainda assim o fluxo deve seguir, mas a contagem de "respondido" depende de haver registros em Resposta.

        if questionario.cena_destino:
            return redirect('narrativa:exibir_cena_paciente', cena_id=questionario.cena_destino.id)
        else:
            if questionario.cena_associada:
                return redirect('narrativa:exibir_cena_paciente', cena_id=questionario.cena_associada.id)
            return redirect('narrativa:paciente_narrativas')

    context = {
        'questionario': questionario
    }
    return render(request, 'questionario.html', context)


# --- VISTAS DE SUPORTE ---

class AdminFAQView(LoginRequiredMixin, TemplateView):
    template_name = "admin_faq.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        return context


class TermosView(TemplateView):
    template_name = "termos.html"


class PoliticaView(TemplateView):
    template_name = "politica.html"


# --- VIEW DE PERFIL CORRIGIDA ---
def perfil_sessao_view(request, narrativa_id):
    session_key = request.session.session_key
    if not session_key:
        return redirect('narrativa:ler_termos')

    narrativa_atual = get_object_or_404(Narrativa, pk=narrativa_id)

    # Recupera o perfil (que é fixo da primeira narrativa visitada nesta sessão)
    try:
        sessao_paciente = SessaoPaciente.objects.get(session_key=session_key)
        nome_perfil = sessao_paciente.narrativa_perfil.titulo if sessao_paciente.narrativa_perfil else "Visitante"
    except SessaoPaciente.DoesNotExist:
        nome_perfil = "Visitante"

    # 1. CÁLCULO DE CENAS (Estritamente da narrativa atual)
    total_cenas = Cena.objects.filter(narrativa=narrativa_atual).count()

    cenas_visitadas = LogVisitaCena.objects.filter(
        session_key=session_key,
        narrativa_associada=narrativa_atual  # Filtro crucial
    ).values('cena_visitada').distinct().count()

    progresso_cenas_pct = 0
    if total_cenas > 0:
        progresso_cenas_pct = int((cenas_visitadas / total_cenas) * 100)
        if progresso_cenas_pct > 100: progresso_cenas_pct = 100

    # 2. CÁLCULO DE QUESTIONÁRIOS (Estritamente da narrativa atual)
    total_questionarios = Questionario.objects.filter(
        cena_associada__narrativa=narrativa_atual
    ).count()

    # Conta questionários que tiveram pelo menos UMA resposta salva nesta sessão
    questionarios_respondidos = Resposta.objects.filter(
        session_key=session_key,
        pergunta__questionario__cena_associada__narrativa=narrativa_atual
    ).values('pergunta__questionario').distinct().count()

    progresso_questionarios_pct = 0
    if total_questionarios > 0:
        progresso_questionarios_pct = int((questionarios_respondidos / total_questionarios) * 100)
        if progresso_questionarios_pct > 100: progresso_questionarios_pct = 100

    context = {
        'narrativa': narrativa_atual,
        'nome_perfil': nome_perfil,

        'cenas_visitadas': cenas_visitadas,
        'total_cenas': total_cenas,
        'progresso_cenas_pct': progresso_cenas_pct,

        'questionarios_respondidos': questionarios_respondidos,
        'total_questionarios': total_questionarios,
        'progresso_questionarios_pct': progresso_questionarios_pct,
    }

    return render(request, 'perfil_sessao.html', context)