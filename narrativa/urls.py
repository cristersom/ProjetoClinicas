from django.urls import path, reverse_lazy
from .views import (
    Narrativas, Homepage, Detalhes, Pesquisa, PerfilView, Criarconta,
    iniciar_jornada_paciente, exibir_cena_paciente, responder_questionario,
    PacienteNarrativas, PacienteDetalhes,

    # --- Vistas importadas ---
    AdminFAQView, TermosView, PoliticaView
)
from django.contrib.auth import views as auth_view

app_name = 'narrativa'

urlpatterns = [
    path('', Homepage.as_view(), name='homepage'),

    # URLs específicas do paciente
    path('paciente/narrativas/', PacienteNarrativas.as_view(), name='paciente_narrativas'),
    path('paciente/narrativa/<int:pk>/', PacienteDetalhes.as_view(), name='paciente_detalhes'),
    path('paciente/iniciar/<int:narrativa_id>/', iniciar_jornada_paciente, name='iniciar_jornada_paciente'),
    path('paciente/cena/<int:cena_id>/', exibir_cena_paciente, name='exibir_cena_paciente'),
    path('paciente/questionario/<int:questionario_id>/', responder_questionario, name='responder_questionario'),

    # URLs do admin/usuário logado
    path('narrativas/', Narrativas.as_view(), name='narrativas'),
    path('narrativas/<int:pk>', Detalhes.as_view(), name='detalhes'),
    path('pesquisa/', Pesquisa.as_view(), name='pesquisa'),
    path('login/', auth_view.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_view.LogoutView.as_view(template_name='logout.html'), name='logout'),
    path('perfil/<int:pk>', PerfilView.as_view(), name='perfil'),
    path('criarconta/', Criarconta.as_view(), name='criarconta'),
    path('mudarsenha/', auth_view.PasswordChangeView.as_view(template_name='perfil.html',
                                                             success_url=reverse_lazy('narrativa:narrativas')),
         name='mudarsenha'),

    # --- Rotas adicionadas ---
    path('ajuda-admin/', AdminFAQView.as_view(), name='admin_faq'),
    path('termos-de-uso/', TermosView.as_view(), name='termos_de_uso'),
    path('politica-de-privacidade/', PoliticaView.as_view(), name='politica_privacidade'),
]