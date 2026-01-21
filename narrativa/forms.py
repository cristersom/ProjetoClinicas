from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Pergunta

class FormHomepage(forms.Form):
    email = forms.EmailField(label=False, widget=forms.EmailInput(attrs={'placeholder': 'Seu e-mail'}))

class CriarContaForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = Usuario
        fields = ('username', 'email')

class PerguntaAdminForm(forms.ModelForm):
    class Meta:
        model = Pergunta
        fields = '__all__'
        widgets = {
            'texto_pergunta': forms.TextInput(attrs={'style': 'width: 100%;', 'placeholder': 'Digite a pergunta...'}),
        }