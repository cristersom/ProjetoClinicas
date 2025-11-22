from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'narrativa'

urlpatterns = [
    # --- Rotas Gerais ---
    path('', views.Homepage.as_view(), name='homepage'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='logout.html'), name='logout'),
    path('criarconta/', views.Criarconta.as_view(), name='criarconta'),
    path('termos/', views.TermosView.as_view(), name='termos_de_uso'),
    path('politica/', views.PoliticaView.as_view(), name='politica_privacidade'),

    # --- Área Logada (Admin/Criador) ---
    path('narrativas/', views.Narrativas.as_view(), name='narrativas'),
    path('narrativa/<int:pk>/', views.Detalhes.as_view(), name='detalhes'),
    path('pesquisa/', views.Pesquisa.as_view(), name='pesquisa'),
    path('perfil/<int:pk>/', views.PerfilView.as_view(), name='perfil'),
    path('ajuda/', views.AdminFAQView.as_view(), name='admin_faq'),

    # --- Fluxo de Aceite de Termos (Middleware) ---
    path('ler_termos/', views.LerTermosView.as_view(), name='ler_termos'),
    path('ler_termos/<int:narrativa_pk>/', views.LerTermosView.as_view(), name='ler_termos_pk'),

    # --- Área do Paciente (Jornada) ---
    path('paciente/narrativas/', views.PacienteNarrativas.as_view(), name='paciente_narrativas'),
    path('paciente/narrativa/<int:pk>/', views.PacienteDetalhes.as_view(), name='paciente_detalhes'),
    path('paciente/iniciar/<int:narrativa_id>/', views.iniciar_jornada_paciente, name='iniciar_jornada_paciente'),
    path('paciente/cena/<int:cena_id>/', views.exibir_cena_paciente, name='exibir_cena_paciente'),
    path('paciente/questionario/<int:questionario_id>/', views.responder_questionario, name='responder_questionario'),

    # --- NOVA ROTA: Perfil de Sessão (Feedback) ---
    path('paciente/perfil/<int:narrativa_id>/', views.perfil_sessao_view, name='perfil_sessao'),
]