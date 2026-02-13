from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from narrativa import views

urlpatterns = [
    # Login direto para o Administrador
    path('admin/login/', admin.site.login),

    # Dashboard Customizado na raiz do Admin
    path('admin/', views.DashboardView.as_view(), name='admin_index'),

    # URLs padrão do Django Admin
    path('admin/', admin.site.urls),

    # Inclui todas as rotas do App Narrativa (incluindo a raiz '')
    path('', include('narrativa.urls', namespace='narrativa')),
]

# Configuração para arquivos de mídia e estáticos
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # No Heroku, o WhiteNoise cuida disso, mas mantemos as rotas para consistência
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)