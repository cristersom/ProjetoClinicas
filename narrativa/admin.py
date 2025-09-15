from django.contrib import admin
from .models import Narrativa, Cena, Usuario
from django.contrib.auth.admin import UserAdmin

campos = list(UserAdmin.fieldsets)
campos. append(
    ("Histórico", {'fields': ('narrativas_vistas', )})
)
UserAdmin. fieldsets = tuple (campos)

# Register your models here.
admin.site.register(Narrativa)
admin.site.register(Cena)
admin.site.register(Usuario, UserAdmin)