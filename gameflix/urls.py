from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from narrativa import views  # Importamos as views da nossa app

urlpatterns = [
    # --- TRUQUE: Intercepta a raiz do admin para mostrar nosso Dashboard ---
    path('admin/', views.DashboardView.as_view(), name='admin_index'),

    # O admin.site.urls continua aqui para gerenciar as outras rotas (/admin/narrativa/..., etc)
    path('admin/', admin.site.urls),

    path('', include('narrativa.urls', namespace='narrativa')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)