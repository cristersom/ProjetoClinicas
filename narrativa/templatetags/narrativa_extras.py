# narrativa/templatetags/narrativa_extras.py
from django import template

register = template.Library()

@register.filter(name='split')
def split(value, key):
    return value.split(key)

# --- NOVO: Adicione este filtro ---
@register.filter(name='strip')
def strip(value):
    return value.strip()
# --- FIM DA ADIÇÃO ---