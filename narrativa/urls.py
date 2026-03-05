from django.urls import path
from . import views

app_name = 'narrativa'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('planos/', views.PlanosView.as_view(), name='planos'),
    path('checkout/<str:price_id>/', views.criar_checkout_sessao, name='criar_checkout_sessao'),
    path('sucesso/', views.sucesso_pagamento, name='sucesso_pagamento'),

    # Rotas obrigatórias para o footer não dar erro
    path('termos/', views.HomeView.as_view(), name='termos_de_uso'),
    path('privacidade/', views.HomeView.as_view(), name='politica_privacidade'),
    path('minhas-narrativas/', views.HomeView.as_view(), name='narrativas'),
]