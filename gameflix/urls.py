from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from narrativa import views

urlpatterns = [
    # O Admin padrão do Django para login direto
    path('admin/login/', admin.site.login),

    # Intercepta a raiz do admin para o seu Dashboard customizado
    path('admin/', views.DashboardView.as_view(), name='admin_index'),

    # Restante das rotas do admin
    path('admin/', admin.site.urls),

    path('', include('narrativa.urls', namespace='narrativa')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)