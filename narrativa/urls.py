# narrativa/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'narrativa'

urlpatterns = [
    # Rotas de Autenticação/Admin
    path('', views.Homepage.as_view(), name='homepage'),
    path('narrativas/', views.Narrativas.as_view(), name='narrativas'),
    path('detalhes/<int:pk>/', views.Detalhes.as_view(), name='detalhes'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='logout.html'), name='logout'),
    # Note: Assumindo que você tem um template 'mudarsenha.html'
    path('mudarsenha/',
         auth_views.PasswordChangeView.as_view(template_name='mudarsenha.html', success_url='/narrativas/'),
         name='mudarsenha'),
    path('perfil/<int:pk>/', views.PerfilView.as_view(), name='perfil'),
    path('criarconta/', views.Criarconta.as_view(), name='criarconta'),
    path('pesquisa/', views.Pesquisa.as_view(), name='pesquisa'),

    # Rotas Legais e Admin
    path('termos/', views.TermosView.as_view(), name='termos_de_uso'),
    path('politica/', views.PoliticaView.as_view(), name='politica_privacidade'),
    path('admin/faq/', views.AdminFAQView.as_view(), name='admin_faq'),

    # Rotas de Aceite dos Termos (NOVO)
    path('ler_termos/', views.LerTermosView.as_view(), name='ler_termos'),
    path('ler_termos/<int:narrativa_pk>/', views.LerTermosView.as_view(), name='ler_termos_pk'),

    # Rotas do Paciente
    path('paciente/narrativas/', views.PacienteNarrativas.as_view(), name='paciente_narrativas'),

    # Rota de Detalhes do Paciente (MODIFICADA: a view agora processa o POST)
    path('paciente/detalhes/<int:pk>/', views.PacienteDetalhes.as_view(), name='paciente_detalhes'),

    # Rota de Iniciar Jornada (AGORA SÓ CHAMADA INTERNAMENTE PELO POST DE PacienteDetalhes)
    path('paciente/jornada/<int:narrativa_id>/iniciar/', views.iniciar_jornada_paciente,
         name='iniciar_jornada_paciente'),
    path('paciente/cena/<int:cena_id>/', views.exibir_cena_paciente, name='exibir_cena_paciente'),
    path('paciente/questionario/<int:questionario_id>/responder/', views.responder_questionario,
         name='responder_questionario'),
]