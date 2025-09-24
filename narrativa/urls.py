# narrativa/urls.py

from django.urls import path, reverse_lazy
# --- MODIFICADO: Inclua iniciar_jornada_paciente na importação ---
from .views import Narrativas, Homepage, Detalhes, Pesquisa, Perfil, Criarconta, iniciar_jornada_paciente, exibir_cena_paciente, responder_questionario
from django.contrib.auth import views as auth_view

app_name = 'narrativa'

urlpatterns = [
    path('', Homepage.as_view(), name='homepage'),
    # --- NOVO: URL para iniciar a jornada do paciente sem login ---
    path('paciente/iniciar/<int:narrativa_id>/', iniciar_jornada_paciente, name='iniciar_jornada_paciente'),
    # -----------------------------------------------------------------
    # --- NOVO: Adicione esta URL para exibir a cena do paciente ---
    path('paciente/cena/<int:cena_id>/', exibir_cena_paciente, name='exibir_cena_paciente'),
    # -----------------------------------------------------------------
    # --- NOVO: Adicione esta URL para a página do questionário ---
    path('paciente/questionario/<int:questionario_id>/', responder_questionario, name='responder_questionario'),
    # ---
    path('narrativas/', Narrativas.as_view(), name='narrativas'),
    path('narrativas/<int:pk>', Detalhes.as_view(), name='detalhes'),
    path('pesquisa/', Pesquisa.as_view(), name='pesquisa'),
    path('login/', auth_view.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_view.LogoutView.as_view(template_name='logout.html'), name='logout'),
    path('perfil/<int:pk>', Perfil.as_view(template_name='perfil.html'), name='perfil'),
    path('criarconta/', Criarconta.as_view(), name='criarconta'),
    path('mudarsenha/', auth_view.PasswordChangeView.as_view(template_name='perfil.html', success_url=reverse_lazy('narrativa:narrativas')), name='mudarsenha'),
]