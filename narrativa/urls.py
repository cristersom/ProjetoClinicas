from django.urls import path
from . import views

app_name = 'narrativa'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('planos/', views.PlanosView.as_view(), name='planos'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('criarconta/', views.LoginView.as_view(), name='criarconta'), # Adicione esta linha!
    path('criar-checkout-sessao/<str:price_id>/', views.criar_checkout_sessao, name='criar_checkout_sessao'),
    path('sucesso/', views.sucesso_pagamento, name='sucesso_pagamento'),
]