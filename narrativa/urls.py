# url - view - template

from django.urls import path, include
from .views import Narrativas, Homepage, Detalhes

app_name = 'narrativa'

urlpatterns = [
    path('', Homepage.as_view(), name='homepage'),
    path('narrativas/', Narrativas.as_view(), name='narrativas'),
    path('narrativas/<int:pk>', Detalhes.as_view(), name='detalhes'),
]