# url - view - template

from django.urls import path, include
from .views import Narrativas, Homepage, Detalhes, Pesquisa, Perfil, Criarconta
from django.contrib.auth import views as auth_view

app_name = 'narrativa'

urlpatterns = [
    path('', Homepage.as_view(), name='homepage'),
    path('narrativas/', Narrativas.as_view(), name='narrativas'),
    path('narrativas/<int:pk>', Detalhes.as_view(), name='detalhes'),
    path('pesquisa/', Pesquisa.as_view(), name='pesquisa'),
    path('login/', auth_view.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_view.LogoutView.as_view(template_name='logout.html'), name='logout'),
    path('perfil/', Perfil.as_view(template_name='perfil.html'), name='perfil'),
    path('criarconta/', Criarconta.as_view(), name='criarconta'),
]