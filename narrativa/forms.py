from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Pergunta # Adicionado Pergunta aos imports
from django import forms

# --- Formulário da Homepage (Original) ---
class FormHomepage(forms.Form):
    email = forms.EmailField(label=False)

# --- Formulário de Criar Conta (Original) ---
class CriarContaForm(UserCreationForm):
    # Adicionamos email ao formulário de criação de conta
    email = forms.EmailField(required=True)

    class Meta:
        model = Usuario
        # Incluímos 'email' nos campos a serem exibidos e salvos
        fields = ('username', 'email') # Removido password1 e password2 daqui, UserCreationForm cuida disso

    # Garante que o email seja salvo
    def save(self, commit=True):
        user = super(CriarContaForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


# --- Formulário Customizado para Pergunta no Admin (Novo) ---
# Obtém as opções originais do model
PERGUNTA_TIPO_CHOICES = list(Pergunta.TIPOS_RESPOSTA)

class PerguntaAdminForm(forms.ModelForm):

    # Adiciona a opção "Selecione o tipo" ao dropdown
    tipo_resposta = forms.ChoiceField(
        choices=[('', 'Selecione o tipo')] + PERGUNTA_TIPO_CHOICES,
        required=True # Campo continua obrigatório
    )

    # Adiciona placeholder ao campo de texto da pergunta
    texto_pergunta = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Digite o texto da pergunta aqui...',
            'style': 'width: 90%;' # Ajusta largura
        }),
        required=True
    )

    class Meta:
        model = Pergunta
        fields = '__all__'