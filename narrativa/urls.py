from django.urls import path
from . import views

app_name = 'narrativa'

urlpatterns = [
    path('', views.Homepage.as_view(), name='home'),
    path('criarconta/', views.Criarconta.as_view(), name='criarconta'),
    path('planos/', views.PlanosView.as_view(), name='planos'),
    path('narrativas/', views.Narrativas.as_view(), name='narrativas'),

    # Rota de Checkout
    path('checkout/<str:price_id>/', views.criar_checkout_sessao, name='checkout'),

    # Outras rotas financeiras
    path('sucesso/', views.pagamento_sucesso, name='sucesso_pagamento'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
]