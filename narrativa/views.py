from django.shortcuts import render, redirect, reverse, get_object_or_404
from .models import Narrativa, Usuario, Cena, Questionario, Pergunta, Resposta
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

class Perfil(LoginRequiredMixin, UpdateView):
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


# --- NOVO: View para iniciar a jornada do paciente (Tarefa 10) ---
def iniciar_jornada_paciente(request, narrativa_id):
    # 1. Encontrar a Narrativa pelo ID
    narrativa = get_object_or_404(Narrativa, pk=narrativa_id)

    # 2. Encontrar a cena inicial desta narrativa
    if not narrativa.cena_inicial:
        # Se por algum motivo a narrativa não tiver uma cena inicial definida,
        # retornamos para a homepage ou exibimos uma mensagem de erro.
        # Por enquanto, vamos para a página de narrativas, mas isso pode ser ajustado.
        return redirect('narrativa:narrativas') # Ou crie um template de erro específico

    # 3. Redirecionar para a exibição da cena inicial.
    # Esta URL 'exibir_cena_paciente' será criada na Tarefa 11.
    return redirect('narrativa:exibir_cena_paciente', cena_id=narrativa.cena_inicial.id)



# narrativa/views.py

# (imports no topo do arquivo)
from django.shortcuts import render, get_object_or_404
from .models import Cena

# ... (outras views) ...

def exibir_cena_paciente(request, cena_id):
    # 1. Busca a cena específica pelo ID (nenhuma mudança aqui)
    cena = get_object_or_404(Cena, pk=cena_id)

    # --- NOVO: Lógica para calcular o progresso ---
    try:
        # Pega a lista de todas as cenas da mesma narrativa, ordenadas por ID
        todas_cenas = list(cena.narrativa.cenas.all().order_by('id'))
        total_cenas = len(todas_cenas)
        # Encontra o índice (posição) da cena atual na lista (+1 para não começar do zero)
        progresso_atual = todas_cenas.index(cena) + 1
        # Calcula o percentual para a barra de progresso
        percentual = int((progresso_atual / total_cenas) * 100)
    except (ValueError, ZeroDivisionError):
        # Caso algo dê errado (ex: narrativa sem cenas), definimos valores padrão
        total_cenas = 0
        progresso_atual = 0
        percentual = 0
    # --- FIM DA LÓGICA DE PROGRESSO ---

    # 2. Empacota a cena e os novos dados de progresso para enviar ao template
    context = {
        'cena': cena,
        'total_cenas': total_cenas,
        'progresso_atual': progresso_atual,
        'percentual': percentual,
    }

    # 3. Renderiza o template com o novo contexto
    return render(request, 'cena_paciente.html', context)


# --- VERSÃO COMPLETA DA VIEW DO QUESTIONÁRIO ---
def responder_questionario(request, questionario_id):
    questionario = get_object_or_404(Questionario, pk=questionario_id)

    if request.method == "POST":
        # Garante que uma sessão anônima exista
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

        # Itera sobre cada pergunta do questionário
        for pergunta in questionario.perguntas.all():
            # Pega a resposta do formulário. O nome do input é 'pergunta_ID'
            # Para checkboxes (múltipla escolha), pegamos uma lista de respostas
            if pergunta.tipo_resposta == "MULTIPLA_ESCOLHA":
                respostas = request.POST.getlist(f'pergunta_{pergunta.id}')
                texto_resposta = ",".join(respostas)  # Junta as várias respostas em um texto só
            else:  # Para todos os outros tipos, pegamos um valor único
                texto_resposta = request.POST.get(f'pergunta_{pergunta.id}')

            # Salva no banco de dados se o paciente respondeu algo
            if texto_resposta:
                Resposta.objects.create(
                    pergunta=pergunta,
                    session_key=session_key,
                    texto_resposta=texto_resposta
                )

        # Redireciona para a homepage após salvar
        return redirect('narrativa:homepage')

    context = {
        'questionario': questionario
    }
    return render(request, 'questionario.html', context)
# ... (fim do seu arquivo views.py)





# def homepage(request):
# return render(request, "homepage.html")

# def narrativas (request):
# context = {}
# lista_narrativas = Narrativa.objects.all()
# context['lista_narrativas'] = lista_narrativas
#     return render(request, "narrativas.html", context)