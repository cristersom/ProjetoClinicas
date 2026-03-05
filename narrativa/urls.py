from django.urls import path
from . import views

app_name = 'narrativa'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('planos/', views.PlanosView.as_view(), name='planos'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('criar-checkout-sessao/<str:price_id>/', views.criar_checkout_sessao, name='criar_checkout_sessao'),
    path('criarconta/', views.LoginView.as_view(), name='criarconta'),
    path('sucesso/', views.sucesso_pagamento, name='sucesso_pagamento'),
    # Rotas de segurança para evitar erro na Navbar
    path('minhas-jornadas/', views.HomeView.as_view(), name='narrativas'),
    path('dashboard/', views.HomeView.as_view(), name='dashboard_admin'),
]