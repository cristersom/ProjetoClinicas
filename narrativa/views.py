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

from .models import Plano, Narrativa, Clinica, Cena, Questionario, Resposta, SessaoPaciente, LogVisitaCena, \
    ConfiguracaoClinica, PagamentoPendente
from .forms import CadastroForm

stripe.api_key = settings.STRIPE_SECRET_KEY
Usuario = get_user_model()
TERMOS_ACEITOS_KEY = getattr(settings, 'TERMOS_ACEITOS_KEY', 'termo_aceite_session')


# --- INSTITUCIONAL E AUTENTICAÇÃO ---

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


@require_http_methods(["GET", "POST"])
def custom_logout(request):
    logout(request)
    # Redireciona limpo para a Home sem erro CSRF
    return redirect('narrativa:home')


class CriarContaView(CreateView):
    model = Usuario
    form_class = CadastroForm
    template_name = 'criarconta.html'
    success_url = reverse_lazy('narrativa:narrativas')

    def get_initial(self):
        initial = super().get_initial()
        email_pre = self.request.GET.get('email') or self.request.session.get('email_pagamento')
        if email_pre:
            initial['email'] = email_pre
        return initial

    def form_valid(self, form):
        email_digitado = form.cleaned_data.get('email')

        pagamento = PagamentoPendente.objects.filter(email__iexact=email_digitado, utilizado=False).first()

        if not pagamento:
            form.add_error('email',
                           "Nenhum plano contratado para este e-mail. Por favor, escolha um plano antes de criar sua conta.")
            return self.form_invalid(form)

        response = super().form_valid(form)
        user = self.object

        if hasattr(user, 'clinica') and user.clinica:
            user.clinica.assinatura_ativa = True
            user.clinica.plano_atual = pagamento.plano
            user.clinica.stripe_customer_id = pagamento.stripe_customer_id
            user.clinica.save()

            pagamento.utilizado = True
            pagamento.save()

            if 'email_pagamento' in self.request.session:
                del self.request.session['email_pagamento']

        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(self.request, "Conta criada e assinatura ativada com sucesso! Bem-vindo ao seu painel.")
        return response


class TermosView(TemplateView):
    template_name = "termos.html"


class PoliticaView(TemplateView):
    template_name = "politica.html"


# --- SAAS E PAGAMENTOS ---

class PlanosView(ListView):
    model = Plano
    template_name = 'planos.html'
    context_object_name = 'planos'


def checkout(request, plano_id):
    plano = get_object_or_404(Plano, id=plano_id)
    domain_url = request.build_absolute_uri('/')[:-1]

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': plano.stripe_price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=domain_url + reverse('narrativa:sucesso_pagamento') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + reverse('narrativa:planos'),
            metadata={'plano_id': plano.id}
        )
        return redirect(checkout_session.url)
    except Exception as e:
        messages.error(request, str(e))
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
            email=email,
            defaults={
                'plano': plano,
                'stripe_customer_id': session.customer,
                'utilizado': False
            }
        )

        user = Usuario.objects.filter(email=email).first()

        if user:
            if hasattr(user, 'clinica') and user.clinica:
                user.clinica.assinatura_ativa = True
                user.clinica.plano_atual = plano
                user.clinica.stripe_customer_id = session.customer
                user.clinica.save()

                pagamento = PagamentoPendente.objects.get(email=email)
                pagamento.utilizado = True
                pagamento.save()

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return render(request, 'pagamento_sucesso.html', {'user': user, 'novo_usuario': False})
        else:
            messages.info(request, "Pagamento confirmado! Crie sua conta com o mesmo e-mail usado na compra.")
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
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        email = session.get('customer_details', {}).get('email')
        plano_id = session.get('metadata', {}).get('plano_id')

        if email and plano_id:
            plano = Plano.objects.filter(id=plano_id).first()

            PagamentoPendente.objects.update_or_create(
                email=email,
                defaults={
                    'plano': plano,
                    'stripe_customer_id': session.get('customer'),
                    'utilizado': False
                }
            )

            user = Usuario.objects.filter(email=email).first()
            if user and hasattr(user, 'clinica') and user.clinica:
                user.clinica.assinatura_ativa = True
                user.clinica.plano_atual = plano
                user.clinica.stripe_customer_id = session.get('customer')
                user.clinica.save()

                pagamento = PagamentoPendente.objects.get(email=email)
                pagamento.utilizado = True
                pagamento.save()

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        clinica = Clinica.objects.filter(stripe_customer_id=customer_id).first()
        if clinica:
            clinica.assinatura_ativa = False
            clinica.save()

    return HttpResponse(status=200)


# --- PAINEL DA CLÍNICA ---

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
        if hasattr(self.request.user, 'clinica') and self.request.user.clinica:
            context['link_portal'] = self.request.build_absolute_uri(
                reverse('narrativa:portal_paciente', args=[self.request.user.clinica.id])
            )
            context['limite_atingido'] = self.request.user.clinica.atingiu_limite_narrativas()
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

    # INJEÇÃO DO CONTEXTO DO ADMIN PARA O MENU NÃO SUMIR
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "admin/dashboard.html"

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
            acessos = LogVisitaCena.objects.filter(narrativa_associada__clinica=clinica, timestamp__gte=trinta_dias) \
                .annotate(dia=TruncDay('timestamp')).values('dia').annotate(total=Count('id')).order_by('dia')

            context['chart_dias_labels'] = json.dumps([item['dia'].strftime('%d/%m') for item in acessos])
            context['chart_dias_data'] = json.dumps([item['total'] for item in acessos])

            top_narrativas = Narrativa.objects.filter(clinica=clinica).order_by('-visualizacoes')[:5]
            context['chart_top_labels'] = json.dumps([n.titulo for n in top_narrativas])
            context['chart_top_data'] = json.dumps([n.visualizacoes for n in top_narrativas])
        else:
            context.update({'kpi_sessoes': 0, 'kpi_respostas': 0, 'kpi_narrativas': 0, 'kpi_finalizadas': 0,
                            'chart_dias_labels': '[]', 'chart_dias_data': '[]', 'chart_top_labels': '[]',
                            'chart_top_data': '[]'})
        return context


class Pesquisa(ListView):
    template_name = "pesquisa.html"
    model = Narrativa

    def get_queryset(self):
        termo = self.request.GET.get('query')
        if termo and hasattr(self.request.user, 'clinica') and self.request.user.clinica:
            return Narrativa.objects.filter(titulo__icontains=termo, clinica=self.request.user.clinica)
        return Narrativa.objects.none()


# --- PORTAL PÚBLICO E PACIENTE ---

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
        self.narrativa_pk = kwargs.get('narrativa_pk')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        aceite = request.POST.get('aceite')
        if aceite == 'true':
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
        narrativa.visualizacoes += 1
        narrativa.save()
        if not request.session.session_key: request.session.create()
        SessaoPaciente.objects.get_or_create(session_key=request.session.session_key,
                                             defaults={'narrativa_perfil': narrativa})
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['relacionados'] = Narrativa.objects.filter(clinica=self.object.clinica).exclude(pk=self.object.pk)[:4]
        return context


def exibir_cena_paciente(request, cena_id):
    cena = get_object_or_404(Cena, id=cena_id)
    if not request.session.session_key: request.session.create()
    LogVisitaCena.objects.create(session_key=request.session.session_key, cena_visitada=cena,
                                 narrativa_associada=cena.narrativa)

    quest = cena.questionarios.first()
    if quest:
        respostas_existentes = Resposta.objects.filter(session_key=request.session.session_key,
                                                       pergunta__questionario=quest).exists()
        if not respostas_existentes:
            return redirect('narrativa:responder_questionario', cena_id=cena.id, questionario_id=quest.id)

    return render(request, 'cena_paciente.html', {'cena': cena})


@require_http_methods(["GET", "POST"])
def responder_questionario(request, cena_id, questionario_id):
    cena = get_object_or_404(Cena, id=cena_id)
    questionario = get_object_or_404(Questionario, id=questionario_id)

    if not request.session.session_key: request.session.create()
    session_key = request.session.session_key

    if request.method == 'POST':
        for pergunta in questionario.perguntas.all():
            valores = request.POST.getlist(f"pergunta_{pergunta.id}")
            if valores:
                for valor in valores:
                    Resposta.objects.create(pergunta=pergunta, session_key=session_key, texto_resposta=valor)
        if questionario.cena_destino:
            return redirect('narrativa:exibir_cena_paciente', cena_id=questionario.cena_destino.id)
        return redirect('narrativa:exibir_cena_paciente', cena_id=cena.id)

    return render(request, 'questionario.html', {'cena': cena, 'questionario': questionario})


def perfil_sessao(request, narrativa_id):
    narrativa = get_object_or_404(Narrativa, id=narrativa_id)
    if not request.session.session_key: request.session.create()
    session_key = request.session.session_key

    nome_perfil = "Paciente"
    try:
        sessao = SessaoPaciente.objects.get(session_key=session_key)
        if sessao.narrativa_perfil: nome_perfil = sessao.narrativa_perfil.titulo
    except SessaoPaciente.DoesNotExist:
        pass

    cenas_visitadas = LogVisitaCena.objects.filter(session_key=session_key, narrativa_associada=narrativa).values(
        'cena_visitada').distinct().count()
    total_cenas = narrativa.cenas.count()
    progresso_cenas_pct = int((cenas_visitadas / total_cenas) * 100) if total_cenas > 0 else 0

    questionarios_respondidos = Resposta.objects.filter(session_key=session_key,
                                                        pergunta__questionario__cena_associada__narrativa=narrativa).values(
        'pergunta__questionario').distinct().count()
    total_questionarios = Questionario.objects.filter(cena_associada__narrativa=narrativa).count()
    progresso_questionarios_pct = int(
        (questionarios_respondidos / total_questionarios) * 100) if total_questionarios > 0 else 0

    return render(request, 'perfil_sessao.html', {
        'narrativa': narrativa,
        'nome_perfil': nome_perfil,
        'cenas_visitadas': cenas_visitadas,
        'total_cenas': total_cenas,
        'progresso_cenas_pct': progresso_cenas_pct,
        'questionarios_respondidos': questionarios_respondidos,
        'total_questionarios': total_questionarios,
        'progresso_questionarios_pct': progresso_questionarios_pct,
    })


def iniciar_jornada_paciente(request, narrativa_id):
    narrativa = get_object_or_404(Narrativa, id=narrativa_id)

    if not request.session.session_key:
        request.session.create()

    SessaoPaciente.objects.get_or_create(
        session_key=request.session.session_key,
        defaults={'narrativa_perfil': narrativa}
    )

    if narrativa.cena_inicial:
        return redirect('narrativa:exibir_cena_paciente', cena_id=narrativa.cena_inicial.id)
    else:
        # SE NÃO TIVER CENA INICIAL, ELE AVISA AO INVÉS DE QUEBRAR!
        messages.warning(request,
                         f"Atenção: A jornada '{narrativa.titulo}' ainda não possui uma Cena Inicial configurada. Acesse a Administração e configure.")
        return redirect('narrativa:narrativas')


def paciente_narrativas_fallback(request):
    if request.session.session_key:
        sessao = SessaoPaciente.objects.filter(session_key=request.session.session_key).first()
        if sessao and sessao.narrativa_perfil and sessao.narrativa_perfil.clinica:
            return redirect('narrativa:portal_paciente', clinica_id=sessao.narrativa_perfil.clinica.id)

    return redirect('narrativa:home')