from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'narrativa'

urlpatterns = [
    # 1. Rota de Planos no TOPO para evitar conflito
    path('planos/', views.PlanosView.as_view(), name='planos'),

    # 2. Área Pública
    path('', views.Homepage.as_view(), name='home'),
    path('login/', views.Homepage.as_view(), name='login'),
    path('criar-conta/', views.Criarconta.as_view(), name='criarconta'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # 3. Financeiro (Protegido)
    path('checkout/<str:price_id>/', views.criar_checkout_sessao, name='checkout'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
    path('pagamento/sucesso/', views.pagamento_sucesso, name='sucesso_pagamento'),

    # 4. Área Logada
    path('narrativas/', views.Narrativas.as_view(), name='narrativas'),
    path('narrativa/<int:pk>/', views.Detalhes.as_view(), name='detalhes'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard_admin'),
    path('perfil/<int:pk>/', views.PerfilView.as_view(), name='perfil'),

    # 5. Outros
    path('explorar/', views.PacienteNarrativas.as_view(), name='paciente_narrativas'),
    path('v/<int:pk>/', views.PacienteDetalhes.as_view(), name='paciente_detalhes'),
    path('termos/', views.TermosView.as_view(), name='termos_de_uso'),
    path('politica/', views.PoliticaView.as_view(), name='politica_privacidade'),
]