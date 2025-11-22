from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages
from .models import Narrativa, Usuario, Cena, Questionario, Pergunta, Resposta, SessaoPaciente, LogVisitaCena
from .forms import CriarContaForm, FormHomepage
from django.views.generic import ListView, DetailView, FormView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import admin

# Nova chave de sessão para rastrear o aceite dos termos
TERMOS_ACEITOS_KEY = 'termos_aceitos'


# --- VIEWS CORRIGIDAS PARA O FLUXO DE TERMOS E PACIENTE ---

class LerTermosView(TemplateView):
    """View que exibe e processa o aceite dos Termos de Uso do Paciente."""
    template_name = "ler_termos.html"

    def get(self, request, *args, **kwargs):
        # Se os termos JÁ foram aceitos, redireciona para a lista de narrativas
        if request.session.get(TERMOS_ACEITOS_KEY, False):
            return redirect('narrativa:paciente_narrativas')

        # Se os termos NÃO foram aceitos, apenas renderiza a tela.
        self.narrativa_pk = kwargs.get('narrativa_pk')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Processa o aceite
        aceite = request.POST.get('aceite', 'false').lower() == 'true'
        self.narrativa_pk = kwargs.get('narrativa_pk')

        if aceite:
            # Marca o aceite na sessão do navegador
            request.session[TERMOS_ACEITOS_KEY] = True
            messages.success(request, "Termos aceitos com sucesso! Bem-vindo(a) à sua jornada.")

            # Redireciona para o destino
            if self.narrativa_pk:
                return redirect('narrativa:iniciar_jornada_paciente', narrativa_id=self.narrativa_pk)
            else:
                return redirect('narrativa:paciente_narrativas')

        # Se houver POST sem aceite (não deve ocorrer com o JS), redireciona para a tela inicial
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
        relacionados = Narrativa.objects.filter(categoria=self.get_object().categoria).order_by('-visualizacoes')[
                       0:5]
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

    def get(self, request, *args, **kwargs):
        # REDIRECIONA SE OS TERMOS NÃO FOREM ACEITOS
        if not request.session.get(TERMOS_ACEITOS_KEY, False):
            return redirect('narrativa:ler_termos')
        return super().get(request, *args, **kwargs)


class PacienteDetalhes(DetailView):
    template_name = "paciente_detalhes.html"
    model = Narrativa

    def get_context_data(self, **kwargs):
        context = super(PacienteDetalhes, self).get_context_data(**kwargs)
        relacionados = Narrativa.objects.filter(categoria=self.get_object().categoria).order_by('-visualizacoes')[
                       0:5]
        context["relacionados"] = relacionados
        return context

    def post(self, request, *args, **kwargs):
        narrativa = self.get_object()

        # REDIRECIONA PARA ACEITE COM PK DE RETORNO
        if not request.session.get(TERMOS_ACEITOS_KEY, False):
            return redirect('narrativa:ler_termos_pk', narrativa_pk=narrativa.pk)

        # Se os termos já estiverem aceitos, continua a iniciar a jornada
        return iniciar_jornada_paciente(request, narrativa.pk)


def iniciar_jornada_paciente(request, narrativa_id):
    narrativa = get_object_or_404(Narrativa, pk=narrativa_id)

    # REDIRECIONA PARA ACEITE COM PK DE RETORNO
    if not request.session.get(TERMOS_ACEITOS_KEY, False):
        return redirect('narrativa:ler_termos_pk', narrativa_pk=narrativa_id)

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

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

    # REDIRECIONA SE OS TERMOS NÃO FOREM ACEITOS
    if not request.session.get(TERMOS_ACEITOS_KEY, False):
        return redirect('narrativa:ler_termos')

    # --- ADICIONADO PARA O RELATÓRIO DE PERCURSO ---
    if request.session.session_key:
        LogVisitaCena.objects.create(
            session_key=request.session.session_key,
            cena_visitada=cena,
            narrativa_associada=cena.narrativa
        )
    # --- FIM DA ADIÇÃO ---

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

    # REDIRECIONA SE OS TERMOS NÃO FOREM ACEITOS
    if not request.session.get(TERMOS_ACEITOS_KEY, False):
        return redirect('narrativa:ler_termos')

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


# --- VISTAS ADICIONADAS PARA O FAQ E PÁGINAS LEGAIS ---

class AdminFAQView(LoginRequiredMixin, TemplateView):
    template_name = "admin_faq.html"

    # --- 2. ADICIONAR O CONTEXTO DO ADMIN MANUALMENTE ---
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Adiciona o contexto do admin (necessário para o layout do Jazzmin)
        context.update(admin.site.each_context(self.request))
        return context
    # --- FIM DA MUDANÇA ---


class TermosView(TemplateView):
    template_name = "termos.html"


class PoliticaView(TemplateView):
    template_name = "politica.html"