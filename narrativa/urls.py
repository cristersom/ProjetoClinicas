from django.urls import path
from . import views

app_name = 'narrativa'

urlpatterns = [
    path('', views.Homepage.as_view(), name='home'),
    path('criarconta/', views.Criarconta.as_view(), name='criarconta'),
    path('planos/', views.PlanosView.as_view(), name='planos'),
    path('narrativas/', views.Narrativas.as_view(), name='narrativas'),

    # Rota Financeira - O nome do parâmetro aqui deve ser price_id
    path('checkout/<str:price_id>/', views.criar_checkout_sessao, name='checkout'),
    path('sucesso/', views.pagamento_sucesso, name='sucesso_pagamento'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
]