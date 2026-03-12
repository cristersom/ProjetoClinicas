from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'narrativa'

urlpatterns = [
    # Páginas Principais
    path('', views.HomeView.as_view(), name='home'),
    path('planos/', views.PlanosView.as_view(), name='planos'),

    # Autenticação
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='narrativa:home'), name='logout'),

    # Sistema
    path('minhas-narrativas/', views.MinhasNarrativasView.as_view(), name='narrativas'),

    # Stripe (Checkout e Webhook)
    path('checkout/<str:price_id>/', views.criar_checkout_sessao, name='criar_checkout_sessao'),
    path('sucesso/', views.sucesso_pagamento, name='sucesso_pagamento'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),

    # Rotas obrigatórias para o footer não dar erro
    path('termos/', views.HomeView.as_view(), name='termos_de_uso'),
    path('privacidade/', views.HomeView.as_view(), name='politica_privacidade'),
]