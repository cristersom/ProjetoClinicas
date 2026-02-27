from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'narrativa'

urlpatterns = [
    # --- ÁREA PÚBLICA ---
    path('', views.Homepage.as_view(), name='home'),
    path('login/', views.Homepage.as_view(), name='login'),
    path('criar-conta/', views.Criarconta.as_view(), name='criarconta'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Planos (Acesso Público para visualização de preços)
    path('planos/', views.PlanosView.as_view(), name='planos'),

    # --- FINANCEIRO E STRIPE (PROTEGIDOS) ---
    # O checkout exige login para vincular a assinatura à clínica correta
    path('checkout/<str:price_id>/', views.criar_checkout_sessao, name='checkout'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
    path('pagamento/sucesso/', views.pagamento_sucesso, name='sucesso_pagamento'),

    # --- ÁREA DO MÉDICO (PROTEGIDA) ---
    path('narrativas/', views.Narrativas.as_view(), name='narrativas'),
    path('narrativa/<int:pk>/', views.Detalhes.as_view(), name='detalhes'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard_admin'),
    path('perfil/<int:pk>/', views.PerfilView.as_view(), name='perfil'),

    # --- ÁREA DO PACIENTE ---
    path('explorar/', views.PacienteNarrativas.as_view(), name='paciente_narrativas'),
    path('v/<int:pk>/', views.PacienteDetalhes.as_view(), name='paciente_detalhes'),
    path('cena/<int:cena_id>/', views.exibir_cena_paciente, name='exibir_cena_paciente'),
    path('responder/<int:questionario_id>/', views.responder_questionario, name='responder_questionario'),
    path('sessao/<int:narrativa_id>/', views.perfil_sessao_view, name='perfil_sessao'),

    # --- LEGAL E POLÍTICAS ---
    path('termos/', views.TermosView.as_view(), name='termos_de_uso'),
    path('politica/', views.PoliticaView.as_view(), name='politica_privacidade'),
    path('aceitar-termos/', views.LerTermosView.as_view(), name='ler_termos'),
]