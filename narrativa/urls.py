from django.urls import path
from . import views

app_name = 'narrativa'

urlpatterns = [
    # --- Institucional e Autenticação ---
    path('', views.HomeView.as_view(), name='home'),
    path('homepage/', views.HomeView.as_view(), name='homepage'),  # Alias para retrocompatibilidade
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('criar-conta/', views.CriarContaView.as_view(), name='criarconta'),
    path('termos/', views.TermosView.as_view(), name='termos_de_uso'),
    path('politica/', views.PoliticaView.as_view(), name='politica_privacidade'),

    # --- SaaS e Pagamentos ---
    path('planos/', views.PlanosView.as_view(), name='planos'),
    path('checkout/<int:plano_id>/', views.checkout, name='checkout'),
    path('sucesso/', views.sucesso_pagamento, name='sucesso_pagamento'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),

    # --- Painel da Clínica (Admin) ---
    path('minhas-narrativas/', views.MinhasNarrativasView.as_view(), name='narrativas'),
    path('narrativa/<int:pk>/', views.Detalhes.as_view(), name='detalhes'),
    path('perfil/<int:pk>/', views.PerfilView.as_view(), name='perfil'),
    path('pesquisa/', views.Pesquisa.as_view(), name='pesquisa'),
    path('ajuda/', views.AdminFAQView.as_view(), name='admin_faq'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard_admin'),

    # --- Portal Exclusivo da Clínica ---
    path('portal/<int:clinica_id>/', views.PortalPacienteView.as_view(), name='portal_paciente'),

    # --- Fluxo Interativo do Paciente ---
    path('ler_termos/', views.LerTermosView.as_view(), name='ler_termos'),
    path('ler_termos/<int:narrativa_pk>/', views.LerTermosView.as_view(), name='ler_termos_pk'),
    path('jornada/<int:pk>/', views.PacienteDetalhesView.as_view(), name='paciente_detalhes'),

    # Rotas de fallback e funcionalidades restauradas:
    path('jornada/<int:narrativa_id>/iniciar/', views.iniciar_jornada_paciente, name='iniciar_jornada_paciente'),
    path('paciente/narrativas/', views.paciente_narrativas_fallback, name='paciente_narrativas'),

    path('cena/<int:cena_id>/', views.exibir_cena_paciente, name='exibir_cena_paciente'),
    path('cena/<int:cena_id>/questionario/<int:questionario_id>/', views.responder_questionario,
         name='responder_questionario'),
    path('jornada/<int:narrativa_id>/resumo/', views.resumo_sessao, name='perfil_sessao'),
]