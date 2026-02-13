from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'narrativa'

urlpatterns = [
    # Rota Raiz - Resolve o erro de 'Not Found' na home
    path('', views.Homepage.as_view(), name='home'),

    # Dashboard e Gestão SaaS
    path('dashboard/', views.DashboardView.as_view(), name='dashboard_admin'),
    path('narrativas/', views.Narrativas.as_view(), name='narrativas'),
    path('detalhes/<int:pk>/', views.Detalhes.as_view(), name='detalhes'),
    path('perfil/<int:pk>/', views.PerfilView.as_view(), name='perfil'),

    # Autenticação e Redirecionamento de Perfil
    path('login/', views.Homepage.as_view(), name='login'),
    path('criarconta/', views.Criarconta.as_view(), name='criarconta'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Resolve o erro /accounts/profile/ enviando para as narrativas
    path('accounts/profile/', views.Narrativas.as_view(), name='perfil_automatico'),

    # Área do Paciente (Jornadas)
    path('paciente/jornadas/', views.PacienteNarrativas.as_view(), name='paciente_narrativas'),
    path('paciente/detalhes/<int:pk>/', views.PacienteDetalhes.as_view(), name='paciente_detalhes'),
    path('paciente/cena/<int:cena_id>/', views.exibir_cena_paciente, name='exibir_cena_paciente'),
    path('paciente/questionario/<int:questionario_id>/', views.responder_questionario, name='responder_questionario'),
    path('paciente/resumo/<int:narrativa_id>/', views.perfil_sessao_view, name='perfil_sessao'),

    # Institucional
    path('termos/', views.TermosView.as_view(), name='termos_de_uso'),
    path('politica/', views.PoliticaView.as_view(), name='politica_privacidade'),
    path('ler_termos/', views.LerTermosView.as_view(), name='ler_termos'),
]