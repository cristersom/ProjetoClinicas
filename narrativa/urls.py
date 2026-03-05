from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'narrativa'

urlpatterns = [
    # Planos primeiro para garantir a prioridade da rota
    path('planos/', views.PlanosView.as_view(), name='planos'),

    # Públicas
    path('', views.Homepage.as_view(), name='home'),
    path('login/', views.Homepage.as_view(), name='login'),
    path('criar-conta/', views.Criarconta.as_view(), name='criarconta'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Financeiro
    path('checkout/<str:price_id>/', views.criar_checkout_sessao, name='checkout'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
    path('pagamento/sucesso/', views.pagamento_sucesso, name='sucesso_pagamento'),

    # Médico
    path('narrativas/', views.Narrativas.as_view(), name='narrativas'),
]