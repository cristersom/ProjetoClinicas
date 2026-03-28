from django.urls import path
from . import views

app_name = 'narrativa'

urlpatterns = [
    # 1. INSTITUCIONAL E AUTENTICAÇÃO
    path('', views.HomeView.as_view(), name='home'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('criar-conta/', views.CriarContaView.as_view(), name='criarconta'),

    # 2. SAAS E PAGAMENTOS (Stripe)
    path('planos/', views.PlanosView.as_view(), name='planos'),
    path('checkout/<str:price_id>/', views.criar_checkout_sessao, name='criar_checkout_sessao'),
    path('sucesso/', views.sucesso_pagamento, name='sucesso_pagamento'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),

    # 3. PAINEL DA CLÍNICA
    path('minhas-narrativas/', views.MinhasNarrativasView.as_view(), name='narrativas'),

    # 4. FLUXO INTERATIVO DO PACIENTE (Usando o seu original!)
    path('jornada/<int:pk>/', views.PacienteDetalhesView.as_view(), name='paciente_detalhes'),
    path('jornada/<int:narrativa_id>/iniciar/', views.iniciar_jornada_paciente, name='iniciar_jornada_paciente'),
    path('cena/<int:cena_id>/', views.exibir_cena_paciente, name='exibir_cena_paciente'),
    path('cena/<int:cena_id>/questionario/<int:questionario_id>/', views.responder_questionario,
         name='responder_questionario'),
    path('jornada/<int:narrativa_id>/perfil/', views.perfil_sessao, name='perfil_sessao'),
]