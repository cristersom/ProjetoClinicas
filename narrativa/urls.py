from django.urls import path
from . import views

app_name = 'narrativa'

urlpatterns = [
    # Públicas
    path('', views.Homepage.as_view(), name='home'),
    path('criar-conta/', views.Criarconta.as_view(), name='criarconta'),

    # Financeiro
    path('planos/', views.PlanosView.as_view(), name='planos'),
    path('checkout/<str:price_id>/', views.criar_checkout_sessao, name='checkout'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),

    # Médico
    path('narrativas/', views.Narrativas.as_view(), name='narrativas'),
    path('narrativa/<int:pk>/', views.Detalhes.as_view(), name='detalhes'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('perfil/<int:pk>/', views.PerfilView.as_view(), name='perfil'),

    # Paciente
    path('explorar/', views.PacienteNarrativas.as_view(), name='paciente_narrativas'),
    path('v/<int:pk>/', views.PacienteDetalhes.as_view(), name='paciente_detalhes'),
    path('cena/<int:cena_id>/', views.exibir_cena_paciente, name='exibir_cena_paciente'),
    path('responder/<int:questionario_id>/', views.responder_questionario, name='responder_questionario'),
    path('sessao/<int:narrativa_id>/', views.perfil_sessao_view, name='perfil_sessao'),

    # Termos
    path('termos/', views.TermosView.as_view(), name='termos'),
    path('politica/', views.PoliticaView.as_view(), name='politica'),
    path('aceitar-termos/', views.LerTermosView.as_view(), name='ler_termos'),
]