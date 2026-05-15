import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model, login, logout
from django.contrib import messages, admin
from django.db.models import Count
from django.db.models.functions import TruncDay
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    Plano, Narrativa, Clinica, Cena, Questionario, Resposta,
    SessaoPaciente, LogVisitaCena, ConfiguracaoClinica, PagamentoPendente
)
from .forms import CadastroForm

# Configuração da Chave da API do Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
Usuario = get_user_model()
TERMOS_ACEITOS_KEY = getattr(settings, 'TERMOS_ACEITOS_KEY', 'termo_aceite_session')


# ==========================================
# VIEWS PÚBLICAS E AUTENTICAÇÃO
# ==========================================
class HomeView(TemplateView):
    template_name = "homepage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['planos'] = Plano.objects.all()
        return context


class LoginView(DjangoLoginView):
    template_name = "login.html"

    def get_success_url(self):
        return reverse_lazy("narrativa:narrativas")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def custom_logout(request):
    logout(request)
    return redirect('narrativa:home')


class CriarContaView(CreateView):
    model = Usuario
    form_class = CadastroForm
    template_name = 'criarconta.html'
    success_url = reverse_lazy('narrativa:narrativas')

    def get_initial(self):
        initial = super().get_initial()
        registro = self.request.session.get('registro_pendente', {})
        email_pre = (self.request.GET.get('email') or self.request.session.get('email_pagamento') or registro.get(
            'email'))
        if email_pre:
            initial['email'] = email_pre
        initial['username'] = registro.get('username')
        initial['nome_clinica'] = registro.get('nome_clinica')
        return initial

    def form_valid(self, form):
        email_digitado = form.cleaned_data.get('email')
        pagamento = PagamentoPendente.objects.filter(email__iexact=email_digitado, utilizado=False).first()

        # Se não há pagamento, guarda na sessão e manda para os planos
        if not pagamento:
            self.request.session['registro_pendente'] = {
                'username': form.cleaned_data.get('username'),
                'email': email_digitado,
                'nome_clinica': self.request.POST.get('nome_clinica'),
                'senha1': self.request.POST.get('senha1'),
                'senha2': self.request.POST.get('senha2'),
            }
            messages.info(self.request, "Dados guardados! Escolha um plano para ativar a sua conta.")
            return redirect('narrativa:planos')

        # Se há pagamento pendente, cria o utilizador
        response = super().form_valid(form)
        user = self.object

        if hasattr(user, 'clinica') and user.clinica:
            user.clinica.assinatura_ativa = True
            user.clinica.plano_atual = pagamento.plano
            user.clinica.stripe_customer_id = pagamento.stripe_customer_id
            user.clinica.save()

            pagamento.utilizado = True
            pagamento.save()

            self.request.session.pop('email_pagamento', None)
            self.request.session.pop('registro_pendente', None)

        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(self.request, "Conta criada e assinatura ativada! Bem-vindo.")
        return response


class TermosView(TemplateView):
    template_name = "termos.html"


class PoliticaView(TemplateView):
    template_name = "politica.html"


# ==========================================
# GESTÃO DE PLANOS E STRIPE
# ==========================================
class PlanosView(ListView):
    model = Plano
    template_name = 'planos.html'
    context_object_name = 'planos'

    def get(self, request, *args, **kwargs):
        if request.GET.get('gerenciar') == '1' and request.user.is_authenticated:
            clinica = getattr(request.user, 'clinica', None)
            if clinica and clinica.stripe_customer_id:
                try:
                    domain_url = request.build_absolute_uri('/')[:-1]
                    portalSession = stripe.billing_portal.Session.create(
                        customer=clinica.stripe_customer_id,
                        return_url=domain_url + reverse('narrativa:planos')
                    )
                    return redirect(portalSession.url)
                except Exception:
                    messages.error(request, "Não foi possível aceder ao portal de gestão. Contacte o suporte.")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated and hasattr(self.request.user, 'clinica') and self.request.user.clinica:
            clinica = self.request.user.clinica
            context['plano_atual'] = clinica.plano_atual if clinica.assinatura_ativa else None
            context['assinatura_ativa'] = clinica.assinatura_ativa
        return context


def checkout(request, plano_id):
    plano = get_object_or_404(Plano, id=plano_id)
    domain_url = request.build_absolute_uri('/')[:-1]

    # Lógica para utilizadores que já têm conta e querem fazer upgrade/downgrade
    if request.user.is_authenticated and hasattr(request.user, 'clinica'):
        clinica = request.user.clinica
        if clinica.assinatura_ativa and clinica.stripe_customer_id:
            try:
                subs = stripe.Subscription.list(customer=clinica.stripe_customer_id, status='active', limit=1)
                if subs.data:
                    sub_id = subs.data[0].id
                    sub_item_id = subs.data[0]['items']['data'][0]['id']
                    portalSession = stripe.billing_portal.Session.create(
                        customer=clinica.stripe_customer_id,
                        return_url=domain_url + reverse('narrativa:planos'),
                        flow_data={
                            "type": "subscription_update_confirm",
                            "subscription_update_confirm": {
                                "subscription": sub_id,
                                "items": [{"id": sub_item_id, "price": plano.stripe_price_id, "quantity": 1}]
                            }
                        }
                    )
                    return redirect(portalSession.url)
                else:
                    portalSession = stripe.billing_portal.Session.create(
                        customer=clinica.stripe_customer_id,
                        return_url=domain_url + reverse('narrativa:planos')
                    )
                    return redirect(portalSession.url)
            except Exception:
                messages.error(request, "Erro ao processar a atualização do plano.")
                return redirect('narrativa:planos')

    # Checkout para Novos Utilizadores ou contas inativas
    try:
        registro = request.session.get('registro_pendente', {})
        customer_email = registro.get('email')

        checkout_kwargs = {
            'payment_method_types': ['card'],
            'line_items': [{'price': plano.stripe_price_id, 'quantity': 1}],
            'mode': 'subscription',
            'success_url': domain_url + reverse('narrativa:sucesso_pagamento') + '?session_id={CHECKOUT_SESSION_ID}',
            'cancel_url': domain_url + reverse('narrativa:planos'),
            'metadata': {'plano_id': plano.id}
        }

        if customer_email:
            checkout_kwargs['customer_email'] = customer_email

        if request.user.is_authenticated and hasattr(request.user,
                                                     'clinica') and request.user.clinica.stripe_customer_id:
            checkout_kwargs['customer'] = request.user.clinica.stripe_customer_id
            checkout_kwargs.pop('customer_email', None)

        checkout_session = stripe.checkout.Session.create(**checkout_kwargs)
        return redirect(checkout_session.url)
    except Exception as e:
        messages.error(request, f"Erro ao ligar à Stripe: {str(e)}")
        return redirect('narrativa:planos')


def sucesso_pagamento(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('narrativa:home')

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        email = session.customer_details.email
        plano_id = session.metadata.get('plano_id')
        plano = Plano.objects.filter(id=plano_id).first()

        PagamentoPendente.objects.update_or_create(
            email=email, defaults={'plano': plano, 'stripe_customer_id': session.customer, 'utilizado': False}
        )

        user = Usuario.objects.filter(email=email).first()

        if user:
            if hasattr(user, 'clinica') and user.clinica:
                user.clinica.assinatura_ativa = True
                user.clinica.plano_atual = plano
                user.clinica.stripe_customer_id = session.customer
                user.clinica.save()

                p_pendente = PagamentoPendente.objects.filter(email=email).first()
                if p_pendente:
                    p_pendente.utilizado = True
                    p_pendente.save()

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return render(request, 'pagamento_sucesso.html', {'criado_agora': False})
        else:
            registro = request.session.get('registro_pendente')
            if registro:
                registro['email'] = email
                form = CadastroForm(registro)
                if form.is_valid():
                    novo_user = form.save()
                    if hasattr(novo_user, 'clinica') and novo_user.clinica:
                        novo_user.clinica.assinatura_ativa = True
                        novo_user.clinica.plano_atual = plano
                        novo_user.clinica.stripe_customer_id = session.customer
                        novo_user.clinica.save()

                        p_pendente = PagamentoPendente.objects.filter(email=email).first()
                        if p_pendente:
                            p_pendente.utilizado = True
                            p_pendente.save()

                    login(request, novo_user, backend='django.contrib.auth.backends.ModelBackend')
                    request.session.pop('registro_pendente', None)
                    return render(request, 'pagamento_sucesso.html', {'criado_agora': True})

            messages.info(request, "Pagamento confirmado! Finalize a sua conta abaixo.")
            return redirect(f"{reverse('narrativa:criarconta')}?email={email}")

    except Exception as e:
        print(f"Erro no sucesso_pagamento: {e}")
        return redirect('narrativa:home')


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except Exception:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        email = session.get('customer_details', {}).get('email')
        plano_id = session.get('metadata', {}).get('plano_id')

        if email and plano_id:
            plano = Plano.objects.filter(id=plano_id).first()
            if plano:
                PagamentoPendente.objects.update_or_create(
                    email=email,
                    defaults={'plano': plano, 'stripe_customer_id': session.get('customer'), 'utilizado': False}
                )
                clinica = Clinica.objects.filter(usuario__email=email).first()
                if clinica:
                    clinica.assinatura_ativa = True
                    clinica.plano_atual = plano
                    clinica.stripe_customer_id = session.get('customer')
                    clinica.save()

    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        price_id = subscription.get('items', {}).get('data', [{}])[0].get('price', {}).get('id')

        clinica = Clinica.objects.filter(stripe_customer_id=customer_id).first()
        if clinica and price_id:
            novo_plano = Plano.objects.filter(stripe_price_id=price_id).first()
            if novo_plano:
                clinica.plano_atual = novo_plano
                # O Stripe envia 'active' quando a assinatura está regular
                clinica.assinatura_ativa = (subscription.get('status') == 'active')
                clinica.save()

    elif event['type'] in ['customer.subscription.deleted', 'customer.subscription.canceled', 'invoice.payment_failed']:
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        clinica = Clinica.objects.filter(stripe_customer_id=customer_id).first()
        if clinica:
            clinica.assinatura_ativa = False
            clinica.save()

    return HttpResponse(status=200)


# ==========================================
# PAINEL DE CONTROLE (CLÍNICA)
# ==========================================
class MinhasNarrativasView(LoginRequiredMixin, ListView):
    model = Narrativa
    template_name = 'narrativas.html'
    context_object_name = 'narrativas'

    def get_queryset(self):
        if hasattr(self.request.user, 'clinica') and self.request.user.clinica:
            return Narrativa.objects.filter(clinica=self.request.user.clinica)
        return Narrativa.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clinica = getattr(self.request.user, 'clinica', None)
        if clinica:
            context['link_portal'] = self.request.build_absolute_uri(
                reverse('narrativa:portal_paciente', args=[clinica.id]))
            context['limite_atingido'] = getattr(self.request, 'limite_atingido', False)
        return context


class Detalhes(LoginRequiredMixin, DetailView):
    model = Narrativa
    template_name = "detalhes.html"


class PerfilView(LoginRequiredMixin, UpdateView):
    model = Usuario
    template_name = "perfil.html"
    fields = ['username', 'email']
    success_url = reverse_lazy('narrativa:narrativas')


class AdminFAQView(LoginRequiredMixin, TemplateView):
    template_name = "admin/faq.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "admin/_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clinica = getattr(self.request.user, 'clinica', None)

        if clinica:
            sessoes_ids = LogVisitaCena.objects.filter(narrativa_associada__clinica=clinica).values_list('session_key',
                                                                                                         flat=True).distinct()
            context['kpi_sessoes'] = sessoes_ids.count()
            context['kpi_respostas'] = Resposta.objects.filter(
                pergunta__questionario__cena_associada__narrativa__clinica=clinica).count()
            context['kpi_narrativas'] = Narrativa.objects.filter(clinica=clinica).count()
            context['kpi_finalizadas'] = 0

            trinta_dias = timezone.now() - timedelta(days=30)
            acessos = LogVisitaCena.objects.filter(narrativa_associada__clinica=clinica,
                                                   timestamp__gte=trinta_dias).annotate(
                dia=TruncDay('timestamp')).values('dia').annotate(total=Count('id')).order_by('dia')

            context['chart_dias_labels'] = json.dumps([item['dia'].strftime('%d/%m') for item in acessos])
            context['chart_dias_data'] = json.dumps([item['total'] for item in acessos])

            top_narrativas = Narrativa.objects.filter(clinica=clinica).order_by('-visualizacoes')[:5]
            context['chart_top_labels'] = json.dumps([n.titulo for n in top_narrativas])
            context['chart_top_data'] = json.dumps([n.visualizacoes for n in top_narrativas])
        else:
            context.update({'kpi_sessoes': 0, 'kpi_respostas': 0, 'kpi_narrativas': 0, 'kpi_finalizadas': 0})
        return context


class Pesquisa(ListView):
    template_name = "pesquisa.html"
    model = Narrativa

    def get_queryset(self):
        termo = self.request.GET.get('query')
        if termo and hasattr(self.request.user, 'clinica') and self.request.user.clinica:
            return Narrativa.objects.filter(titulo__icontains=termo, clinica=self.request.user.clinica)
        return Narrativa.objects.none()


# ==========================================
# PORTAL DO PACIENTE (FRONT-END DA CLÍNICA)
# ==========================================
class PortalPacienteView(ListView):
    template_name = 'portal_paciente.html'
    context_object_name = 'narrativas'

    def get_queryset(self):
        self.clinica = get_object_or_404(Clinica, id=self.kwargs['clinica_id'])
        return Narrativa.objects.filter(clinica=self.clinica).order_by('-data_criacao')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clinica'] = self.clinica
        return context


class LerTermosView(TemplateView):
    template_name = "ler_termos.html"

    def get(self, request, *args, **kwargs):
        if request.session.get(TERMOS_ACEITOS_KEY, False):
            pk = kwargs.get('narrativa_pk')
            if pk: return redirect('narrativa:paciente_detalhes', pk=pk)
            return redirect('narrativa:home')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.POST.get('aceite') == 'true':
            request.session[TERMOS_ACEITOS_KEY] = True
            pk = kwargs.get('narrativa_pk')
            if pk: return redirect('narrativa:paciente_detalhes', pk=pk)
            return redirect('narrativa:home')
        return redirect('narrativa:ler_termos')


class PacienteDetalhesView(DetailView):
    model = Narrativa
    template_name = "paciente_detalhes.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        narrativa = self.get_object()

        # Incrementa visualizações
        narrativa.visualizacoes += 1
        narrativa.save()

        # UPGRADE: Segurança de Sessão. Garante que o cookie de sessão é criado antes de avançar.
        if not request.session.session_key:
            request.session.create()

        SessaoPaciente.objects.get_or_create(
            session_key=request.session.session_key,
            defaults={'narrativa_perfil': narrativa}
        )
        return response

    def post(self, request, *args, **kwargs):
        # Resolve o Erro HTTP 405 (Method Not Allowed)
        return redirect('narrativa:iniciar_jornada_paciente', narrativa_id=self.get_object().id)


def exibir_cena_paciente(request, cena_id):
    # UPGRADE: Otimização Extrema de Banco de Dados. Carrega todas as dependências da cena num único hit.
    cena = get_object_or_404(
        Cena.objects.prefetch_related('questionarios__perguntas', 'escolhas', 'escolhas__cena_destino'),
        id=cena_id
    )

    if not request.session.session_key:
        request.session.create()

    LogVisitaCena.objects.create(
        session_key=request.session.session_key,
        cena_visitada=cena,
        narrativa_associada=cena.narrativa
    )

    questionarios_status = []
    pendentes = 0

    # Valida se os questionários associados a esta cena já foram respondidos
    for quest in cena.questionarios.all():
        respondido = Resposta.objects.filter(
            session_key=request.session.session_key,
            pergunta__questionario=quest
        ).exists()

        questionarios_status.append({
            'id': quest.id,
            'titulo': quest.titulo,
            'respondido': respondido
        })

        if not respondido:
            pendentes += 1

    # Permite prosseguir se não houver questionários pendentes
    context = {
        'cena': cena,
        'questionarios_status': questionarios_status,
        'pode_prosseguir': (pendentes == 0)
    }

    return render(request, 'cena_paciente.html', context)


@require_http_methods(["GET", "POST"])
def responder_questionario(request, cena_id, questionario_id):
    cena = get_object_or_404(Cena, id=cena_id)
    questionario = get_object_or_404(Questionario, id=questionario_id)

    if not request.session.session_key:
        request.session.create()

    if request.method == 'POST':
        for pergunta in questionario.perguntas.all():
            valores = request.POST.getlist(f"pergunta_{pergunta.id}")
            for valor in valores:
                if valor.strip():  # Salva apenas se o utilizador digitou/selecionou algo
                    Resposta.objects.create(
                        pergunta=pergunta,
                        session_key=request.session.session_key,
                        texto_resposta=valor
                    )

        # Retorna sempre para a cena onde estava (onde o questionário está ancorado)
        return redirect('narrativa:exibir_cena_paciente', cena_id=cena.id)

    return render(request, 'questionario.html', {'cena': cena, 'questionario': questionario})


def perfil_sessao(request, narrativa_id):
    narrativa = get_object_or_404(Narrativa, id=narrativa_id)
    sk = request.session.session_key
    nome_perfil = "Paciente"

    try:
        sessao = SessaoPaciente.objects.get(session_key=sk)
        if sessao.narrativa_perfil:
            nome_perfil = sessao.narrativa_perfil.titulo
    except Exception:
        pass

    visitadas = LogVisitaCena.objects.filter(session_key=sk, narrativa_associada=narrativa).values(
        'cena_visitada').distinct().count()
    total = narrativa.cenas.count()
    prog_cenas = int((visitadas / total) * 100) if total > 0 else 0

    respondidos = Resposta.objects.filter(session_key=sk,
                                          pergunta__questionario__cena_associada__narrativa=narrativa).values(
        'pergunta__questionario').distinct().count()
    total_q = Questionario.objects.filter(cena_associada__narrativa=narrativa).count()
    prog_q = int((respondidos / total_q) * 100) if total_q > 0 else 0

    return render(request, 'perfil_sessao.html', {
        'narrativa': narrativa,
        'nome_perfil': nome_perfil,
        'progresso_cenas_pct': prog_cenas,
        'progresso_questionarios_pct': prog_q
    })


def iniciar_jornada_paciente(request, narrativa_id):
    narrativa = get_object_or_404(Narrativa, id=narrativa_id)

    if not request.session.session_key:
        request.session.create()

    SessaoPaciente.objects.get_or_create(
        session_key=request.session.session_key,
        defaults={'narrativa_perfil': narrativa}
    )

    # LÓGICA INTELIGENTE: Pega a cena inicial OU a primeira cena vinculada à jornada
    cena_alvo = narrativa.cena_inicial

    if not cena_alvo and narrativa.cenas.exists():
        cena_alvo = narrativa.cenas.first()

    if cena_alvo:
        return redirect('narrativa:exibir_cena_paciente', cena_id=cena_alvo.id)

    # Se a narrativa estiver literalmente vazia
    messages.warning(request, "Esta jornada ainda não tem cenas configuradas.")
    return redirect('narrativa:portal_paciente', clinica_id=narrativa.clinica.id if narrativa.clinica else 0)


def paciente_narrativas_fallback(request):
    if request.session.session_key:
        sessao = SessaoPaciente.objects.filter(session_key=request.session.session_key).first()
        if sessao and sessao.narrativa_perfil and sessao.narrativa_perfil.clinica:
            return redirect('narrativa:portal_paciente', clinica_id=sessao.narrativa_perfil.clinica.id)
    return redirect('narrativa:home')