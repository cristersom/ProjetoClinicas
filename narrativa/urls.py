from django.urls import path
from . import views

app_name = 'narrativa'

urlpatterns = [
    # Institucional e Autenticação
    path('', views.HomeView.as_view(), name='home'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('criar-conta/', views.CriarContaView.as_view(), name='criarconta'),

    # Documentação e LGPD
    path('termos/', views.TermosView.as_view(), name='termos'),
    path('politica/', views.PoliticaView.as_view(), name='politica'),
    path('faq/', views.AdminFAQView.as_view(), name='faq'),

    # SaaS e Pagamentos
    path('planos/', views.PlanosView.as_view(), name='planos'),
    path('checkout/<int:plano_id>/', views.checkout, name='checkout'),
    path('sucesso-pagamento/', views.sucesso_pagamento, name='sucesso_pagamento'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),

    # Painel da Clínica
    path('minhas-narrativas/', views.MinhasNarrativasView.as_view(), name='narrativas'),
    path('detalhes/<int:pk>/', views.Detalhes.as_view(), name='detalhes'),
    path('perfil/', views.PerfilView.as_view(), name='perfil'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('pesquisa/', views.Pesquisa.as_view(), name='pesquisa'),

    # Portal Público e Paciente
    path('portal/<int:clinica_id>/', views.PortalPacienteView.as_view(), name='portal_paciente'),
    path('jornada/<int:narrativa_pk>/termos/', views.LerTermosView.as_view(), name='ler_termos'),
    path('jornada/<int:pk>/', views.PacienteDetalhesView.as_view(), name='paciente_detalhes'),
    path('cena/<int:cena_id>/', views.exibir_cena_paciente, name='exibir_cena_paciente'),
    path('cena/<int:cena_id>/questionario/<int:questionario_id>/', views.responder_questionario,
         name='responder_questionario'),
    path('jornada/<int:narrativa_id>/perfil/', views.perfil_sessao, name='perfil_sessao'),
    path('jornada/<int:narrativa_id>/iniciar/', views.iniciar_jornada_paciente, name='iniciar_jornada_paciente'),
    path('jornada/continuar/', views.paciente_narrativas_fallback, name='paciente_narrativas_fallback'),
]